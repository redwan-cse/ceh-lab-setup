import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    from lab_scripts import LabScripts
except ImportError:
    LabScripts = None


class ScriptWorkflow:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.state = self.folder / '.state'
        self.state.mkdir()
        self.messages = []
        self.commands = []

    def redact(self, text):
        return text.replace('known-test-api-secret', '[REDACTED]')

    def write(self, name, text):
        (self.state / name).write_text(text, encoding='utf-8')

    def emit(self, text):
        self.messages.append(text)

    def execute(self, command, runner):
        self.commands.append(command)
        return runner(command)


class LabScriptsTests(unittest.TestCase):
    def test_ai_review_can_approve_owned_readonly_script_without_human_prompt(self):
        from unittest.mock import Mock
        self.scripts.approval_reviewer=Mock(return_value=True)
        self.scripts.input_reader=Mock(side_effect=AssertionError('Human prompt not expected'))
        value=self.scripts.write('ai_readonly','python','print("SYNTHETIC_AI_SCRIPT_OK")')
        self.assertIn('SYNTHETIC_AI_SCRIPT_OK',self.scripts.run(value['script']))
        self.scripts.approval_reviewer.assert_called_once()
    def test_language_change_keeps_the_version_series(self):
        first=self.scripts.write('language_change','python','print(1)')
        second=self.scripts.write('language_change_2','powershell','Write-Output 2')
        self.assertEqual(first['script'],'scripts_language_change_1.py')
        self.assertEqual(second['script'],'scripts_language_change_2.ps1')

    def test_edit_name_with_model_added_version_uses_original_series(self):
        first=self.scripts.write('check','python','print(1)')
        second=self.scripts.write('check_2','python','print(2)')
        self.assertEqual(first['script'],'scripts_check_1.py')
        self.assertEqual(second['script'],'scripts_check_2.py')

    def test_same_unchanged_version_reuses_session_approval(self):
        value=self.scripts.write('reuse','python',"print('session-approved')")
        with patch('builtins.input',return_value='yes') as confirm:
            self.assertIn('session-approved',self.scripts.run(value['script']))
            self.assertIn('session-approved',self.scripts.run(value['script']))
            self.assertEqual(confirm.call_count,1)

    def setUp(self):
        tty=patch('terminal_ui.sys.stdin.isatty',return_value=True)
        tty.start();self.addCleanup(tty.stop)
        self.assertIsNotNone(LabScripts, 'LabScripts implementation is missing')
        self.temp = tempfile.TemporaryDirectory(prefix='lab scripts ')
        self.addCleanup(self.temp.cleanup)
        self.workflow = ScriptWorkflow(self.temp.name)
        self.scripts = LabScripts(self.workflow)

    def test_versions_preserve_original_and_survive_new_manager(self):
        original = self.workflow.folder / 'original.py'
        original.write_text('user original', encoding='utf-8')
        values = [self.scripts.write('demo', 'python', f'print({n})') for n in range(3)]
        self.assertEqual([v['script'] for v in values], ['scripts_demo_1.py', 'scripts_demo_2.py', 'scripts_demo_3.py'])
        next_value = LabScripts(self.workflow).write('scripts_demo_2.py', 'python', 'print(4)')
        self.assertEqual(next_value['script'], 'scripts_demo_4.py')
        self.assertEqual(Path(values[0]['path']).read_text(encoding='utf-8'), 'print(0)')
        self.assertEqual(original.read_text(), 'user original')
        index = json.loads((self.workflow.state / 'scripts-index.json').read_text())
        self.assertEqual(index[values[0]['script']]['sha256'], hashlib.sha256(b'print(0)').hexdigest())
        self.assertEqual(sum(message.count('print(0)') for message in self.workflow.messages), 1)

    def test_python_runs_only_after_explicit_approval_and_logs(self):
        value = self.scripts.write('hello', 'py', "import sys; print('hello'); print('error', file=sys.stderr)")
        with patch('builtins.input', return_value='yes'):
            result = self.scripts.run(value['script'])
        self.assertIn('hello', result)
        self.assertIn('error', result)
        self.assertIn('Exit code: 0', result)
        self.assertEqual(len(self.workflow.commands), 1)

    def test_decline_or_eof_never_executes_source(self):
        value = self.scripts.write('marker', 'python', "from pathlib import Path; Path('marker').touch()")
        for answer in ('no', 'y', ''):
            with patch('builtins.input', return_value=answer):
                self.assertIn('declined', self.scripts.run(value['path']).lower())
        with patch('builtins.input', side_effect=EOFError):
            self.assertIn('declined', self.scripts.run(value['script']).lower())
        self.assertFalse((self.workflow.folder / 'scripts/marker').exists())

    def test_modified_or_unowned_script_is_refused(self):
        value = self.scripts.write('hello', 'python', 'print(1)')
        Path(value['path']).write_text('print(2)', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'changed|hash'):
            self.scripts.run(value['script'])
        rogue = self.workflow.folder / 'scripts/scripts_rogue_1.py'
        rogue.write_text('print(3)', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.scripts.run(rogue.name)

    def test_content_changed_during_approval_is_refused(self):
        value = self.scripts.write('hello', 'python', 'print(1)')
        def approve(prompt):
            Path(value['path']).write_text('print(2)', encoding='utf-8')
            return 'yes'
        with patch('builtins.input', side_effect=approve):
            with self.assertRaisesRegex(ValueError, 'changed|hash'):
                self.scripts.run(value['script'])

    def test_unsafe_names_and_secrets_never_write(self):
        for name in ('../outside', 'dir/name', 'dir\\name', 'C:bad', '.hidden', 'x & whoami', 'CON', ''):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.scripts.write(name, 'python', 'print(1)')
        with self.assertRaisesRegex(ValueError, 'credential|secret'):
            self.scripts.write('secret', 'python', 'known-test-api-secret')
        self.assertFalse((self.workflow.folder / 'outside.py').exists())

    def test_existing_version_is_not_overwritten_or_adopted(self):
        folder = self.workflow.folder / 'scripts'
        folder.mkdir()
        existing = folder / 'scripts_demo_1.py'
        existing.write_text('user file', encoding='utf-8')
        value = self.scripts.write('demo', 'python', 'print(2)')
        self.assertEqual(value['script'], 'scripts_demo_2.py')
        self.assertEqual(existing.read_text(), 'user file')
        with self.assertRaises(ValueError):
            self.scripts.run(existing.name)

    def test_three_language_extensions_and_native_commands(self):
        for language, extension in [('python', '.py'), ('bash', '.sh'), ('powershell', '.ps1'), ('batch', '.bat'), ('cmd', '.cmd')]:
            value = self.scripts.write('native', language, 'echo test')
            self.assertTrue(value['script'].endswith(extension))
        path = self.workflow.folder / 'scripts/scripts_native_1.py'
        self.assertEqual(self.scripts._command(path, 'python'), [sys.executable, path.name])
        with patch('lab_scripts._windows', return_value=False), patch('lab_scripts.shutil.which', side_effect=lambda name: '/usr/bin/' + name):
            self.assertEqual(self.scripts._command(path.with_suffix('.sh'), 'bash'), ['/usr/bin/bash', path.with_suffix('.sh').name])
            self.assertEqual(self.scripts._command(path.with_suffix('.ps1'), 'powershell'), ['/usr/bin/pwsh', '-NoProfile', '-NonInteractive', '-File', path.with_suffix('.ps1').name])
            with self.assertRaisesRegex(ValueError, 'Windows'):
                self.scripts._command(path.with_suffix('.bat'), 'batch')

    def test_unavailable_runtime_explains_without_installing(self):
        value = self.scripts.write('hello', 'bash', 'echo hello')
        with patch('lab_scripts._windows', return_value=False), patch('lab_scripts.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'installed|compatible'):
                self.scripts.run(value['script'])

    def test_symlink_script_folder_is_refused(self):
        outside = self.workflow.folder / 'outside'
        outside.mkdir()
        try:
            (self.workflow.folder / 'scripts').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink privileges unavailable')
        with self.assertRaises((ValueError, RuntimeError)):
            self.scripts.write('hello', 'python', 'print(1)')
        self.assertEqual(list(outside.iterdir()), [])

    def test_timeout_stops_the_launched_script(self):
        value = self.scripts.write('timeout', 'python', "import time; print('started', flush=True); time.sleep(30)")
        with patch('builtins.input', return_value='yes'), patch('lab_scripts._TIMEOUT_SECONDS', 0.1):
            result = self.scripts.run(value['script'])
        self.assertIn('Timed out', result)
        self.assertIn('started', result)
        self.assertNotIn('Exit code: None', result)

    @unittest.skipUnless(os.name == 'nt', 'Windows native runtime test')
    def test_windows_batch_handles_spaces_in_working_directory(self):
        value = self.scripts.write('batch', 'batch', '@echo off\r\necho native-batch-ok\r\n')
        with patch('builtins.input', return_value='yes'):
            result = self.scripts.run(value['script'])
        self.assertIn('native-batch-ok', result)
        self.assertIn('Exit code: 0', result)

    @unittest.skipUnless(os.name == 'nt', 'Windows native runtime test')
    def test_windows_powershell_uses_only_child_process_policy(self):
        value = self.scripts.write('powershell', 'powershell', "Write-Output 'native-powershell-ok'")
        argv = self.scripts._command(Path(value['path']), 'powershell')
        self.assertIn('-ExecutionPolicy', argv)
        self.assertEqual(argv[argv.index('-ExecutionPolicy') + 1], 'Bypass')
        with patch('builtins.input', return_value='yes'):
            result = self.scripts.run(value['script'])
        if 'running scripts is disabled' in result or 'PSSecurityException' in result:
            self.assertNotIn('Exit code: 0', result)
        else:
            self.assertIn('native-powershell-ok', result)
            self.assertIn('Exit code: 0', result)
    def test_child_stdin_is_closed(self):
        value = self.scripts.write('stdin', 'python', 'import sys; print(repr(sys.stdin.read()))')
        with patch('builtins.input', return_value='yes'):
            self.assertIn("''", self.scripts.run(value['script']))


if __name__ == '__main__':
    unittest.main()
