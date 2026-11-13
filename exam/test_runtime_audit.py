"""Opt-in installed-CLI integration checks; mocks the API and uses temp reports."""
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
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
            visible=io.StringIO()
            with patch('exam_workflow.Workflow',return_value=workflow),patch.object(workflow,'start_transcript'),patch.object(handler.client.chat.completions,'create',side_effect=create),patch.object(handler.Handler,'get_completion',handler.Handler.get_completion),patch.object(guard,'execute_command',guard.execute_command),patch('sys.argv',arguments),patch('sys.stdin',io.StringIO('')),patch('builtins.input',side_effect=AssertionError('Unexpected approval prompt')),patch('sys.stdout',visible):
                try:exam_runtime.main()
                except SystemExit as exc:self.assertIn(exc.code,(0,None))
            records=[json.loads(line) for line in (workflow.state/'evidence-index.jsonl').read_text().splitlines()]
            self.assertEqual(len(records),1)
            self.assertIn('    OUTPUT:\n    Exit code: 0',workflow.log.read_text())
            self.assertEqual(len(calls),1 if shell else 2)
            self.assertNotIn('[API]',visible.getvalue())
            self.assertNotIn('Automatically running',visible.getvalue())
            self.assertIn('[API]',workflow.log.read_text())

    def test_shell_command_is_audited(self):self.run_cli(True)
    def test_tool_command_is_audited(self):self.run_cli(False)

    def run_limit_case(self,interactive,answer):
        import exam_runtime
        import sgpt.handlers.handler as handler
        guard=importlib.import_module('sgpt.shellgpt_command_guard' if os.name=='nt' else 'sgpt.linux_command_guard')
        sent=[];output=[]
        def create(**kwargs):
            sent.append(kwargs)
            value=({'role':'assistant','tool_calls':[{'id':'budget-test','type':'function','function':{
                'name':'execute_shell_command','arguments':'{"shell_command":"audit_budget_fixture"}'}}]}
                if len(sent)==1 else {'role':'assistant','content':'RESUMED_OK'})
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(model_dump=lambda **_:value))])
        def entry():
            h=handler.Handler(SimpleNamespace(name='ShellGPT',role='System administration assistant'),False)
            output.extend(h.get_completion('unused',0,1,[dict(role='user',content='Limit test')],functions=[{}]))
        class Input(io.StringIO):
            def isatty(self):return interactive
        with tempfile.TemporaryDirectory() as directory:
            workflow=Workflow(Path(directory))
            with patch('exam_workflow.Workflow',return_value=workflow),patch.object(workflow,'start_transcript'), \
                    patch.object(handler.client.chat.completions,'create',side_effect=create), \
                    patch.object(handler.Handler,'get_completion',handler.Handler.get_completion), \
                    patch.object(guard,'execute_command',return_value='Exit code: 0, Output: saved-result') as execute, \
                    patch('sgpt.app.entry_point',side_effect=entry),patch('sys.stdin',Input('')), \
                    patch('builtins.input',return_value=answer) as prompt, \
                    patch('sys.argv',['sgpt','--profile','openrouter-deepseek','--tool-rounds','1','Limit test']):
                if not interactive:
                    with self.assertRaises(exam_runtime.ToolLimitReached):exam_runtime.main()
                else:exam_runtime.main()
            self.assertEqual(execute.call_count,1)
            self.assertEqual(prompt.call_count,1 if interactive else 0)
            status=json.loads((workflow.state/'last-task.json').read_text())
            continued=interactive and answer=='yes'
            self.assertEqual(len(sent),2 if continued else 1)
            self.assertEqual(status['completed'],continued)
            if continued:
                self.assertIn('RESUMED_OK',''.join(output))
                self.assertIn('saved-result',str(sent[1]['messages']))
            else:self.assertEqual(status['review'],'tool-limit')

    def test_limit_prompt_continues_in_same_context(self):self.run_limit_case(True,'yes')
    def test_limit_decline_keeps_task_incomplete(self):self.run_limit_case(True,'no')
    def test_limit_with_closed_input_cannot_approve_continuation(self):self.run_limit_case(False,'yes')

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

    def test_real_repl_opens_replies_and_resumes_after_tool_only_message(self):
        from providers import OPENROUTER_BASE
        code=r'''
import io,json,os,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
source=Path(sys.argv[1]);home=Path(sys.argv[2]);phase=sys.argv[3];resuming=phase=='resume'
sys.path.insert(0,str(source));calls=[]
class Terminal(io.StringIO):
    def isatty(self):return True
def create(self,**kwargs):
    assert phase!='show','Displaying saved chat must not call the provider'
    calls.append(kwargs)
    text=str(kwargs['messages'])
    if resuming:
        assert 'SAVED_REPLY_FIRST' in text and 'SAVED_REPLY_SECOND' in text
        assert 'thought_signature' in text and 'OFFLINE_TOOL_RESULT' in text
        value={'role':'assistant','content':'RESTORED_REPLY'}
    elif len(calls)==1:
        value={'role':'assistant','tool_calls':[{'id':'repl-tool','type':'function','function':{'name':'execute_shell_command','arguments':'{"shell_command":"offline_repl_fixture"}'},'extra_content':{'google':{'thought_signature':'offline-signature'}}}]}
    else:value={'role':'assistant','content':'SAVED_REPLY_FIRST' if len(calls)==2 else 'SAVED_REPLY_SECOND'}
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(model_dump=lambda **_:value),finish_reason='stop')])
with patch('pathlib.Path.home',return_value=home),patch('getpass.getpass',side_effect=AssertionError('Unexpected key prompt')),patch('socket.socket.connect',side_effect=AssertionError('Unexpected network request')),patch('openai.resources.chat.completions.Completions.create',create):
    import exam_runtime,exam_workflow
    import importlib
    guard=importlib.import_module('sgpt.shellgpt_command_guard' if os.name=='nt' else 'sgpt.linux_command_guard')
    with patch.object(exam_workflow,'desktop',return_value=home/'Desktop'),patch.object(exam_workflow,'local_ip',return_value='127.0.0.1'),patch.object(guard,'execute_command',lambda command:'Exit code: 0\nOFFLINE_TOOL_RESULT'),patch('sys.stdin',Terminal('')),patch('typer.prompt',side_effect=['resume turn','exit()'] if resuming else ['first turn','second turn','exit()']):
        sys.argv=['sgpt','--show-chat','challenge5'] if phase=='show' else ['sgpt','--challenge','5','--repl','challenge5']
        exam_runtime.main()
    assert len(calls)==(0 if phase=='show' else 1 if resuming else 3)
'''
        # Use the genuine REPL/ChatSession/CLI; only input, API and command runner
        # are fixtures. In particular, do not replace the sgpt app entry point.
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);config=home/'.config/shell_gpt_exam';config.mkdir(parents=True)
            settings=dict(OPENAI_API_KEY='offline-router',API_BASE_URL=OPENROUTER_BASE,EXAM_PROFILE='openrouter-deepseek',ROLE_STORAGE_PATH=str(config/'roles'),CHAT_CACHE_PATH=str(config/'chats'),CACHE_PATH=str(config/'cache'))
            (config/'.sgptrc').write_text(''.join(f'{k}={v}\n' for k,v in settings.items()))
            (config/'provider-keys.json').write_text(json.dumps(dict(openrouter='offline-router')))
            functions=config/'functions';functions.mkdir()
            (functions/'fixture.py').write_text('''from pydantic import BaseModel
class Function(BaseModel):
    shell_command: str
    @classmethod
    def execute(cls, shell_command):return "Fixture must use the runtime command wrapper"
    @classmethod
    def openai_schema(cls):return {"type":"function","function":{"name":"execute_shell_command","parameters":{"type":"object","properties":{"shell_command":{"type":"string"}},"required":["shell_command"]}}}
''')
            # The runner mock imports sgpt before main sets profile paths.
            environment=dict(os.environ,HOME=str(home),USERPROFILE=str(home),CHAT_CACHE_PATH=str(config/'chats/openrouter-deepseek'))
            for phase in ('fresh','resume','show'):
                result=subprocess.run([sys.executable,'-c',code,str(Path(__file__).parent),str(home),phase],env=environment,input='',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if phase!='show':self.assertIn('Entering REPL mode',result.stdout)
                else:self.assertIn('OFFLINE_TOOL_RESULT',result.stdout)
                if phase=='resume':self.assertIn('RESTORED_REPLY',result.stdout)
            saved=json.loads((config/'chats/openrouter-deepseek/challenge5').read_text())
            self.assertTrue(any('tool_calls' in message and 'content' not in message for message in saved))
            self.assertIn('RESTORED_REPLY',str(saved))
            self.assertEqual(len(list((home/'Desktop/CEH-Exam/127.0.0.1/sessions').iterdir())),3)

    def test_same_chat_name_is_isolated_between_profiles(self):
        from providers import STEP_BASE
        code=r'''
import json,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
source=Path(sys.argv[1]);home=Path(sys.argv[2]);profile=sys.argv[3]
sys.path.insert(0,str(source))
calls=[]
def create(self,**kwargs):
    calls.append(kwargs)
    other='stepfun' if profile=='openrouter-deepseek' else 'openrouter-deepseek'
    assert not any('REPLY_'+other in str(m.get('content','')) for m in kwargs['messages'])
    value=dict(role='assistant',content='REPLY_'+profile)
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(model_dump=lambda **kw:value),finish_reason='stop')])
with patch('pathlib.Path.home',return_value=home),patch('getpass.getpass',side_effect=AssertionError('Unexpected credential prompt')),patch('socket.socket.connect',side_effect=AssertionError('Unexpected network request')),patch('openai.resources.chat.completions.Completions.create',create):
    import exam_runtime,exam_workflow
    with patch.object(exam_workflow,'desktop',return_value=home/'Desktop'),patch.object(exam_workflow,'local_ip',return_value='127.0.0.1'),patch.object(exam_workflow.Workflow,'start_transcript'):
        sys.argv=['sgpt','--profile',profile,'--no-functions','--chat','shared-name','test message']
        exam_runtime.main()
    from sgpt.config import cfg
    assert cfg.config_path==home/'.config'/'shell_gpt_exam'/'.sgptrc', 'CLI used a real config path'
    assert len(calls)==1, 'Expected exactly one intercepted completion'
'''
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);config=home/'.config/shell_gpt_exam';config.mkdir(parents=True)
            settings=dict(OPENAI_API_KEY='offline-step',API_BASE_URL=STEP_BASE,EXAM_PROFILE='stepfun',
                          ROLE_STORAGE_PATH=str(config/'roles'),CHAT_CACHE_PATH=str(config/'legacy-chats'),CACHE_PATH=str(config/'legacy-cache'))
            (config/'.sgptrc').write_text(''.join(f'{k}={v}' + chr(10) for k,v in settings.items()))
            (config/'provider-keys.json').write_text(json.dumps(dict(stepfun='offline-step',openrouter='offline-router')))
            # sgpt uses expanduser, while exam_runtime uses Path.home. Isolate both.
            environment=dict(os.environ,HOME=str(home),USERPROFILE=str(home))
            for profile in ('openrouter-deepseek','stepfun','openrouter-deepseek','stepfun'):
                result=subprocess.run([sys.executable,'-c',code,str(Path(__file__).parent),str(home),profile],env=environment,input='',capture_output=True,text=True,timeout=45)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            for profile in ('openrouter-deepseek','stepfun'):
                saved=(config/'chats'/profile/'shared-name').read_text()
                self.assertIn('REPLY_'+profile,saved)
                other='stepfun' if profile=='openrouter-deepseek' else 'openrouter-deepseek'
                self.assertNotIn('REPLY_'+other,saved)

if __name__=='__main__':unittest.main()
