"""Session isolation, shared host facts and quiet terminal regression checks."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from exam_workflow import Workflow


class SessionOutputTests(unittest.TestCase):
    def test_sessions_isolate_logs_findings_and_command_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            old=root/'terminal.md';old.write_text('OLD EVIDENCE')
            first=Workflow(root,session=True,challenge='5')
            second=Workflow(root,session=True,challenge='6')
            third=Workflow(root,session=True,challenge='5')
            self.assertEqual(first.folder.parent,root/'sessions')
            self.assertTrue(first.folder.name.startswith('challenge-5_'))
            self.assertNotEqual(first.folder,third.folder)
            self.assertNotEqual(first.state,second.state)
            first.execute('synthetic inspection',lambda _: 'Exit code: 0\nFLAG_FIVE')
            first.finding('FLAG_FIVE','Observed in synthetic command output')
            self.assertNotIn('FLAG_FIVE',second.log.read_text())
            self.assertEqual(second.findings.read_text(),'')
            with self.assertRaises(ValueError):second.finding('FLAG_FIVE','From another session without supplied evidence')
            second.finding('FLAG_REMOTE','User reports result from another machine',user_evidence='Other machine returned FLAG_REMOTE')
            self.assertIn('FLAG_REMOTE',second.findings.read_text())
            self.assertNotIn('FLAG_REMOTE',first.findings.read_text())
            self.assertEqual(old.read_text(),'OLD EVIDENCE')

    def test_host_facts_and_optional_tool_path_survive_new_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);tools=root/'tools';tools.mkdir()
            (tools/'synthetic.exe').write_text('not executable')
            first=Workflow(root,session=True)
            first.write('network-info.json',json.dumps(dict(host='fixture',local_ipv4=['10.0.0.4'])))
            first.set_tools_path(str(tools),explicit=True)
            second=Workflow(root,session=True)
            self.assertEqual(second.network_data()['host'],'fixture')
            self.assertIn('synthetic.exe',second.find_tools('synthetic'))
            self.assertEqual(json.loads(second.context())['details_file'],str(root/'.state/network-info.json'))

    def test_challenge_labels_from_user_text_and_explicit_option_are_safe(self):
        from exam_workflow import challenge_label
        self.assertEqual(challenge_label('Solve challenge #5 now'),'challenge-5')
        self.assertEqual(challenge_label('Challenge 06: inspect this file'),'challenge-6')
        self.assertEqual(challenge_label('generic request',explicit='7'),'challenge-7')
        self.assertIsNone(challenge_label('Scan port 445'))
        with self.assertRaises(ValueError):challenge_label('',explicit='../escape')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):Workflow(Path(directory),session=True,challenge='../escape')

    def test_diagnostics_are_logged_without_hiding_commands_results_or_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            w=Workflow(Path(directory));output=io.StringIO()
            with redirect_stdout(output):
                w.diagnostic('[API] {"reasoning_tokens":123,"cost_usd":0.01}')
                w.emit('Approval required: installation')
                w.execute('synthetic inspection',lambda _:'Exit code: 0\nACTUAL_OUTPUT')
            self.assertNotIn('[API]',output.getvalue())
            self.assertIn('Approval required:',output.getvalue())
            self.assertIn('COMMAND: synthetic inspection',output.getvalue())
            self.assertIn('ACTUAL_OUTPUT',output.getvalue())
            self.assertIn('reasoning_tokens',w.log.read_text())
            w.verbose=True
            with redirect_stdout(output):w.diagnostic('[API] verbose enabled')
            self.assertIn('[API] verbose enabled',output.getvalue())

    def test_quiet_initialization_review_does_not_append_token_usage(self):
        from types import SimpleNamespace
        response=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='All local checks passed.'))],usage=SimpleNamespace(prompt_tokens=100,completion_tokens=50))
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_:response)))
        with tempfile.TemporaryDirectory() as directory:
            w=Workflow(Path(directory))
            self.assertEqual(w.review(client,'fixture'),'All local checks passed.')


if __name__=='__main__':unittest.main()
