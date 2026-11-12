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
            records=[json.loads(line) for line in (workflow.state/'evidence-index.jsonl').read_text().splitlines()]
            self.assertEqual(len(records),1)
            self.assertIn('OUTPUT:\nExit code: 0',workflow.log.read_text())
            self.assertEqual(len(calls),1 if shell else 2)

    def test_shell_command_is_audited(self):self.run_cli(True)
    def test_tool_command_is_audited(self):self.run_cli(False)

    def run_repl_reviews(self,shell=False):
        import exam_runtime
        import sgpt.handlers.handler as handler
        guard=importlib.import_module('sgpt.shellgpt_command_guard' if os.name=='nt' else 'sgpt.linux_command_guard')
        command='Get-Location' if os.name=='nt' else 'pwd'
        sent=[]
        def create(**kwargs):
            sent.append(kwargs)
            text='Independent review' if kwargs['model']=='gemini-4-carbon' else command if shell else 'Driver answer'
            message=SimpleNamespace(content=text,model_dump=lambda **kw:dict(role='assistant',content=text))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])
        def entry():
            role=SimpleNamespace(name='ShellGPT',role='System administration assistant')
            h=handler.Handler(role,False)
            for turn in ('first task','second task'):
                messages=[dict(role='system',content='Base role'),dict(role='user',content=turn)]
                list(h.get_completion('unused',0,1,messages,functions=None))
                if shell:guard.run_command(command)
        with tempfile.TemporaryDirectory() as directory:
            workflow=Workflow(Path(directory))
            arguments=['sgpt','--profile','gemini-mix','--repl','offline']+(['--shell'] if shell else [])
            with patch('exam_workflow.Workflow',return_value=workflow),patch.object(workflow,'start_transcript'),patch('setup_exam.load_keys',return_value={'gemini':'offline-placeholder'}),patch.object(handler.client.chat.completions,'create',side_effect=create),patch.object(handler.Handler,'get_completion',handler.Handler.get_completion),patch.object(guard,'execute_command',guard.execute_command),patch.object(guard,'run_command',guard.run_command),patch('sgpt.app.entry_point',side_effect=entry),patch('sys.argv',arguments),patch('sys.stdin',io.StringIO('')):
                exam_runtime.main()
            reviews=[kw for kw in sent if kw['model']=='gemini-4-carbon']
            self.assertEqual(len(reviews),2)
            self.assertIn('second task',reviews[1]['messages'][1]['content'])
            self.assertNotIn('first task',reviews[1]['messages'][1]['content'])
            self.assertNotIn('tools',reviews[0])

    def test_each_repl_turn_gets_one_carbon_review(self):self.run_repl_reviews()

    def test_each_shell_repl_execution_gets_one_carbon_review(self):self.run_repl_reviews(True)

if __name__=='__main__':unittest.main()
