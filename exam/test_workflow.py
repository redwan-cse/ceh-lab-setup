from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from exam_workflow import PlainTee, Workflow, discovery_scope


class WorkflowTests(unittest.TestCase):
    def test_commands_logged_and_key_redacted(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder),secret='dummy-key')
            result=w.execute('pwd',lambda command:'Exit code: 0, Output:\nFLAG123 dummy-key')
            self.assertIn('FLAG123',result)
            self.assertNotIn('dummy-key',w.log.read_text())
            self.assertNotIn('dummy-key',result)
            self.assertIn('    OUTPUT:\n    Exit code: 0, Output:\n    FLAG123 [REDACTED]',w.log.read_text())
            self.assertEqual({p.name for p in Path(folder).iterdir() if p.is_file()},{'terminal.md','findings.txt'})
            w.finding('FLAG123','Read from the command output')
            self.assertEqual((Path(folder)/'findings.txt').read_text(),'Flag: FLAG123\nHow found: Read from the command output\n\n')

    def test_unsupported_finding_is_not_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            with self.assertRaises(ValueError):w.finding('invented','Guessed it')
            self.assertEqual((Path(folder)/'findings.txt').read_text(),'')

    def test_user_reported_finding_can_be_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            w.finding('FLAG_GUI','User read it in the GUI',user_evidence='I found FLAG_GUI')
            w.finding('FLAG_GUI','User read it in the GUI',user_evidence='I found FLAG_GUI')
            self.assertEqual((Path(folder)/'findings.txt').read_text().count('Flag:'),1)

    def test_log_failure_prevents_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder));w.log.unlink();w.log.mkdir()
            with self.assertRaises(OSError):w.execute('pwd',lambda cmd:self.fail('ran without log'))

    def test_discovery_requires_small_explicit_range(self):
        for value in ('','0.0.0.0/0','10.0.0.0/8','::/0'):
            with self.assertRaises(ValueError):discovery_scope(value)
        self.assertEqual(str(discovery_scope('10.10.10.0/24')),'10.10.10.0/24')

    def test_catalog_does_not_execute_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);tools=root/'tools';tools.mkdir()
            (tools/'emt.exe').write_text('fixture, not executable')
            w=Workflow(root/'report');w.index_tools(tools)
            self.assertIn('emt.exe',w.find_tools('emt'))

    def test_init_shortcut_makes_no_sgpt_or_api_import(self):
        import builtins
        import exam_runtime
        original=builtins.__import__
        def checked_import(name,*args,**kwargs):
            if name.startswith('sgpt'):self.fail('Local initialization imported an API handler')
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder);config=home/'.config/shell_gpt_exam';config.mkdir(parents=True)
            (config/'.sgptrc').write_text('OPENAI_API_KEY=\n')
            with patch('exam_runtime.Path.home',return_value=home),patch('sys.argv',['sgpt','--init-lab','--local-only']),patch('exam_workflow.Workflow') as w,patch('builtins.__import__',side_effect=checked_import):
                exam_runtime.main()
                w.return_value.initialize.assert_called_once_with(None,False,None)

    def test_init_review_is_one_bounded_request(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder));w.write('network-info.json',json.dumps(dict(host='test',local_ipv4=['10.0.0.1'],checks=[])))
            calls=[]
            def create(**kwargs):
                calls.append(kwargs)
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Review: scope not supplied.'))],usage=None)
            client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
            w.review(client,'gemini-4-carbon')
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0]['reasoning_effort'],'low')
            self.assertEqual(calls[0]['max_completion_tokens'],1536)
            self.assertNotIn('tools',calls[0])
            self.assertLessEqual(len(calls[0]['messages'][1]['content']),5000)
            self.assertFalse((Path(folder)/'init-review.txt').exists())

    def test_default_filing_uses_ip_and_keeps_internal_state_off_desktop(self):
        import exam_workflow
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch('exam_workflow.desktop',return_value=root/'Desktop'),patch('exam_workflow.local_ip',return_value='10.0.0.4'),patch('exam_workflow.state_root',return_value=root/'private-state'):
                w=Workflow()
                self.assertEqual(w.folder,root/'Desktop/CEH-Exam/10.0.0.4')
                self.assertEqual(w.state,root/'private-state/10.0.0.4')
                other=Workflow(target_ip='10.0.0.8')
                self.assertEqual(other.folder.name,'10.0.0.8')
                with self.assertRaises(ValueError):Workflow(target_ip='../other')

    def test_assistant_text_is_not_command_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            w.append(w.log,'Assistant guessed FLAG_FAKE\n')
            with self.assertRaises(ValueError):w.finding('FLAG_FAKE','Not observed')

    def test_command_output_is_saved_as_readable_text_without_ansi(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            w.execute('inspection',lambda command:'Exit code: 0\n\x1b[31mFLAG_COLOR\x1b[0m')
            self.assertNotIn('\x1b',w.log.read_text())
            w.finding('FLAG_COLOR','Actual colored command output')
            self.assertIn('FLAG_COLOR',w.findings.read_text())

    def test_context_does_not_send_full_inventory(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            w.write('network-info.txt',json.dumps(dict(host='lab',scope='10.0.0.0/24',local_network='PRIVATE_DETAIL '*5000)))
            self.assertLessEqual(len(w.context()),1000)
            self.assertNotIn('PRIVATE_DETAIL',w.context())

    def test_network_discovery_is_not_run_before_logging(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            def logged(command,runner):
                if command.startswith('Explicit lab TCP'):raise OSError('logging unavailable')
                return 'local fixture'
            with patch.object(w,'execute',side_effect=logged),patch('exam_workflow.socket.create_connection',side_effect=AssertionError('unlogged probe')):
                with self.assertRaises(OSError):w.initialize('10.0.0.0/30',discover=True)

    def test_changed_scope_does_not_relabel_previous_hosts(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder))
            w.write('network-info.json',json.dumps(dict(scope='10.0.0.0/24',observed_hosts=[dict(ip='10.0.0.2')],discovered_at='old')))
            with patch.object(w,'execute',return_value='Exit code: 0\nlocal fixture'):w.initialize('10.1.0.0/24')
            self.assertNotIn('observed_hosts',w.network_data())

    def test_terminal_transcript_redacts_split_key_and_removes_escapes(self):
        import io
        with tempfile.TemporaryDirectory() as folder:
            w=Workflow(Path(folder),secret='dummy-key');tee=PlainTee(io.StringIO(),w)
            tee.write('\x1b[31mdummy-');tee.flush();tee.write('key\x1b[0m\x1b]8;;https://example.com\x1b\\ link\x1b]8;;\x1b\\\n')
            result=w.log.read_text()
            self.assertTrue(result.endswith('    [REDACTED] link\n'))

    def test_markdown_keeps_legacy_evidence_and_quotes_terminal_content(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);legacy=root/'terminal.txt';legacy.write_text('LEGACY_FLAG\n')
            w=Workflow(root)
            w.append(w.state/'evidence-index.jsonl',json.dumps(dict(id='legacy',start=0,end=len('LEGACY_FLAG\n')))+'\n')
            w.finding('LEGACY_FLAG','Previously captured command output')
            w.execute('inspection',lambda cmd:'Exit code: 0\n# untrusted heading\n```\nNEW_FLAG')
            w.finding('NEW_FLAG','New captured command output')
            self.assertEqual(legacy.read_text(),'LEGACY_FLAG\n')
            text=w.log.read_text()
            self.assertTrue(text.startswith('# ShellGPT terminal evidence'))
            self.assertIn('    # untrusted heading\n    ```',text)
            records=[json.loads(line) for line in (w.state/'evidence-index.jsonl').read_text().splitlines()]
            self.assertEqual(records[-1]['file'],'terminal.md')

if __name__=='__main__':unittest.main()
