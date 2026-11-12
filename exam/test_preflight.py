import unittest
from unittest.mock import patch
import preflight
import setup_exam
from pathlib import Path
import tempfile
import subprocess
import os
import venv
from types import SimpleNamespace


class PreflightTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Windows PowerShell native stderr handling')
    def test_windows_missing_package_probe_reaches_consent(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);private=home/'CEHLab/shellgpt-exam/venv'
            venv.create(private,with_pip=False)
            shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
            result=subprocess.run([str(shell),'-NoProfile','-File',str(Path(__file__).parent/'Setup-Exam.ps1'),'-NoKeyPrompt'],input='',capture_output=True,text=True,env=dict(os.environ,LOCALAPPDATA=str(home)),timeout=30)
            output=result.stdout+result.stderr
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Required setup:',output)
            self.assertIn('Interactive approval required',output)
            self.assertNotIn('Traceback (most recent call last)',output)
            self.assertFalse((home/'CEHLab/shellgpt-python').exists())

    @unittest.skipUnless(os.name=='nt','Windows PowerShell native failure handling')
    def test_windows_failed_probe_reaches_consent_without_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);private=home/'CEHLab/shellgpt-exam/venv/Scripts/python.exe'
            private.parent.mkdir(parents=True);private.write_text('invalid executable fixture')
            shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
            result=subprocess.run([str(shell),'-NoProfile','-File',str(Path(__file__).parent/'Setup-Exam.ps1'),'-NoKeyPrompt'],input='',capture_output=True,text=True,env=dict(os.environ,LOCALAPPDATA=str(home)),timeout=30)
            output=result.stdout+result.stderr
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Required setup:',output)
            self.assertIn('Interactive approval required',output)
            self.assertEqual(private.read_text(),'invalid executable fixture')
            self.assertFalse((home/'CEHLab/shellgpt-exam/python-runtime').exists())
            self.assertFalse((home/'CEHLab/shellgpt-python').exists())

    def test_broken_private_venv_is_preserved_before_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);private=root/'venv';private.mkdir()
            executable=private/('Scripts/python.exe' if preflight.os.name=='nt' else 'bin/python')
            executable.parent.mkdir();executable.write_text('broken executable fixture')
            (root/'exam_runtime.py').write_text('"""ShellGPT exam entry point; owned fixture."""')
            with patch.object(setup_exam,'ROOT',root),patch('setup_exam.subprocess.run',return_value=SimpleNamespace(returncode=1)),patch('setup_exam.venv.create') as create:
                setup_exam.prepare_venv()
            create.assert_called_once_with(private,with_pip=True)
            backups=list(root.glob('venv.before-repair-*'))
            self.assertEqual(len(backups),1)
            self.assertEqual((backups[0]/executable.relative_to(private)).read_text(),'broken executable fixture')

    def test_ready_environment_does_not_prompt_or_install(self):
        with patch('preflight.missing_packages',return_value=[]),patch('preflight.shutil.which',return_value='/usr/bin/ip'),patch('preflight.subprocess.run',side_effect=AssertionError('unexpected install')):
            self.assertTrue(preflight.ensure(True,approve=lambda plan:self.fail('unexpected prompt')))

    def test_declining_the_single_plan_installs_nothing(self):
        plans=[]
        with patch('preflight.missing_packages',return_value=['shell-gpt==1.5.1']),patch('preflight.subprocess.run',side_effect=AssertionError('unexpected install')):
            self.assertFalse(preflight.ensure(False,approve=lambda plan:plans.append(plan) or False))
        self.assertEqual(plans,[['shell-gpt==1.5.1']])

    def test_noninteractive_input_never_approves_installation(self):
        with patch('preflight.sys.stdin.isatty',return_value=False),patch('builtins.input',side_effect=AssertionError('unexpected prompt')):
            self.assertFalse(preflight.consent(['fixture']))

    def test_shared_python_is_never_modified(self):
        with patch('preflight.missing_packages',return_value=['shell-gpt==1.5.1']),patch('preflight.subprocess.run',side_effect=AssertionError('system pip executed')):
            self.assertFalse(preflight.ensure(False,approve=lambda plan:True))


if __name__=='__main__':unittest.main()
