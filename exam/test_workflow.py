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
            self.assertNotIn('dummy-key',(Path(folder)/'commands.log').read_text())
            self.assertNotIn('dummy-key',result)
            self.assertIn('OUTPUT:\nExit code: 0, Output:\nFLAG123 [REDACTED]',(Path(folder)/'commands.txt').read_text())
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
            self.assertTrue((Path(folder)/'init-review.txt').exists())

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
            result=(Path(folder)/'terminal.txt').read_text()
            self.assertEqual(result,'[REDACTED] link\n')

if __name__=='__main__':unittest.main()
