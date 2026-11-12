"""Opt-in installed-CLI integration checks; mocks the API and uses temp reports."""
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from exam_workflow import Workflow


@unittest.skipUnless(os.getenv('EXAM_OFFLINE_INTEGRATION')=='1','Run explicitly in the installed exam venv')
class RuntimeAuditTests(unittest.TestCase):
    def run_cli(self,shell):
        import exam_runtime
        import sgpt.handlers.handler as handler
        guard=importlib.import_module('sgpt.shellgpt_command_guard' if os.name=='nt' else 'sgpt.linux_command_guard')
        command='Get-Location' if os.name=='nt' else 'pwd'
        calls=[]
        class Message:
            def __init__(self,value):self.value=value
            def model_dump(self,**kwargs):return self.value
        def create(**kwargs):
            calls.append(kwargs)
            if shell:value=dict(role='assistant',content=command)
            elif len(calls)==1:
                call=dict(id='audit-test',type='function',
                          function=dict(name='execute_shell_command',arguments=json.dumps(dict(shell_command=command))),
                          extra_content=dict(google=dict(thought_signature='offline-fixture')))
                value=dict(role='assistant',tool_calls=[call])
            else:value=dict(role='assistant',content='OFFLINE_TOOL_DONE')
            return SimpleNamespace(choices=[SimpleNamespace(message=Message(value))])
        with tempfile.TemporaryDirectory() as directory:
            workflow=Workflow(Path(directory))
            arguments=['sgpt','--no-cache']+(['--no-functions','--shell'] if shell else [])+['Offline integration fixture']
            with patch('exam_workflow.Workflow',return_value=workflow),patch.object(workflow,'start_transcript'),patch.object(handler.client.chat.completions,'create',side_effect=create),patch.object(handler.Handler,'get_completion',handler.Handler.get_completion),patch.object(guard,'execute_command',guard.execute_command),patch('sys.argv',arguments),patch('sys.stdin',io.StringIO('')),patch('builtins.input',side_effect=AssertionError('Unexpected approval prompt')):
                try:exam_runtime.main()
                except SystemExit as exc:self.assertIn(exc.code,(0,None))
            records=[json.loads(line) for line in workflow.log.read_text().splitlines()]
            self.assertEqual(len([r for r in records if r['event']=='result']),1)
            self.assertIn('Exit code: 0',records[-1]['output'])
            self.assertIn('OUTPUT:\nExit code: 0', (Path(directory)/'commands.txt').read_text())
            self.assertEqual(len(calls),1 if shell else 2)

    def test_shell_command_is_audited(self):self.run_cli(True)
    def test_tool_command_is_audited(self):self.run_cli(False)

if __name__=='__main__':unittest.main()
