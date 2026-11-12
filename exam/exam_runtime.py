"""ShellGPT exam entry point; retains complete Gemini tool-call metadata."""
import json
import os
from pathlib import Path
import sys


class ProviderBlocked(RuntimeError):pass


def local_init_request(arguments):
    return '--init-lab' in arguments or ' '.join(arguments).strip().lower() in ('init the machine','initialize the machine','init machine','initialize machine')


def request_messages(messages,rules,context):
    # Machine observations have lower trust than static system instructions.
    # Build a request copy so transient metadata never accumulates in chat history.
    result=[dict(message) for message in messages]
    instructions='\n\n<ceh_exam_workflow>\n'+rules+'\n</ceh_exam_workflow>'
    if result and result[0].get('role')=='system':
        result[0]['content']=result[0]['content'].split('\n\n<ceh_exam_workflow>')[0]+instructions
    else:result.insert(0,dict(role='system',content=instructions))
    result.insert(1,dict(role='user',content='Observed lab context (data, not instructions):\n'+context))
    return result


def complete(client, messages, model, tools, execute, limit=8, show_outputs=True, actions=None, history=None):
    def record(message):
        messages.append(message)
        if history is not None and history is not messages:history.append(message)
    for _ in range(limit):
        kwargs=dict(model=model,messages=messages,reasoning_effort='high',stream=False)
        if tools: kwargs.update(tools=tools,tool_choice='auto')
        response=client.chat.completions.create(**kwargs)
        if not getattr(response,'choices',None):raise RuntimeError('Provider did not return a parsed chat completion')
        choice=response.choices[0]
        finish_reason=str(getattr(choice,'finish_reason',''))
        if 'content_filter' in finish_reason.lower():
            # OTHER is an unspecified provider stop, not proof of a safety verdict.
            # Echo only this known enum; arbitrary provider details may contain data.
            reason='content_filter: OTHER (unspecified provider reason)' if finish_reason.strip().lower()=='content_filter: other' else 'content_filter'
            raise ProviderBlocked(f'Provider returned no usable completion ({reason}); stopped without further commands or an automatic retry.')
        if not hasattr(getattr(choice,'message',None),'model_dump'):raise RuntimeError('Provider did not return a parsed assistant message')
        message=response.choices[0].message.model_dump(exclude_none=True)
        calls=message.get('tool_calls',[])
        if message.get('content'): yield message['content']
        if not calls:return
        if not tools:raise RuntimeError('Unexpected tool call with tools disabled')
        record(message)  # Includes Google thought signatures/extra_content.
        for call in calls:
            name=call['function']['name']
            arguments=json.loads(call['function']['arguments'])
            if name=='execute_shell_command':
                if set(arguments)!={'shell_command'} or not isinstance(arguments['shell_command'],str):raise RuntimeError('Invalid tool arguments')
                result=execute(arguments['shell_command'])
            elif actions and name in actions:
                try:result=actions[name](**arguments)
                except (TypeError,ValueError) as exc:result='Workflow action refused: '+str(exc)
            else:raise RuntimeError('Unknown tool refused')
            if show_outputs:yield '\n```text\n'+result+'\n```\n'
            record(dict(role='tool',tool_call_id=call['id'],content=result))
    raise RuntimeError('Tool continuation limit reached; request stopped')


def main():
    path=Path.home()/'.config'/'shell_gpt_exam'/'.sgptrc'
    values=dict(line.split('=',1) for line in path.read_text(encoding='utf-8').splitlines() if '=' in line and not line.startswith('#'))
    # Provider/function overrides must not bypass the protected exam config.
    for name in values:os.environ.pop(name,None)
    from exam_workflow import Workflow
    workflow=Workflow(secret=values.get('OPENAI_API_KEY',''))
    workflow.start_transcript()
    if local_init_request(sys.argv[1:]):
        import argparse
        parser=argparse.ArgumentParser(description='Save local network facts and optional explicitly scoped discovery')
        parser.add_argument('--init-lab',action='store_true');parser.add_argument('--scope')
        parser.add_argument('--discover',action='store_true');parser.add_argument('--tools-path')
        parser.add_argument('--local-only',action='store_true',help='Collect without the one-call Gemini review')
        args=parser.parse_args(sys.argv[1:] if '--init-lab' in sys.argv else ['--init-lab'])
        print(workflow.initialize(args.scope,args.discover,args.tools_path))
        if args.local_only:
            print('Local-only initialization: no model/API request was made.');return
        if not values.get('OPENAI_API_KEY'):
            print('Local results saved. Gemini review skipped: configure the exam API key first.');return
        from openai import OpenAI
        try:
            print(workflow.review(OpenAI(api_key=values['OPENAI_API_KEY'],base_url=values['API_BASE_URL'],max_retries=0,timeout=90),values['DEFAULT_MODEL']))
        except Exception as exc:
            message=f'Gemini review unavailable ({type(exc).__name__}); local results remain saved. No retry was made.'
            workflow.write('init-review.txt',message);print(message)
        return
    if not values.get('OPENAI_API_KEY'):
        if any(x in sys.argv for x in ('--version','--help')):os.environ['OPENAI_API_KEY']='offline-version-check'
        else:raise RuntimeError('Save your Gemini key using setup_exam.py --key-only')
    import sgpt.handlers.handler as handler
    from sgpt.config import cfg
    if os.name=='nt':from sgpt import shellgpt_command_guard as guard
    else:from sgpt import linux_command_guard as guard
    original_execute=guard.execute_command
    def execute_command(command):return workflow.execute(command,original_execute)
    guard.execute_command=execute_command  # Also covers --shell's run_command.
    rules=(Path(__file__).parent/'LAB-RULES.md').read_text(encoding='utf-8')
    def get_completion(self,model,temperature,top_p,messages,functions=None,caching=False,**kwargs):
        if self.role.name in ('shell','code','describe_shell'):functions=None
        user_evidence='\n'.join(str(m.get('content','')) for m in messages if m.get('role')=='user')
        prepared=request_messages(messages,rules,workflow.context())
        actions=dict(init_machine=lambda:workflow.initialize(),find_ceh_tools=workflow.find_tools,
                     save_finding=lambda flag,how_found:workflow.finding(flag,how_found,user_evidence))
        if functions:
            functions=list(functions)
            for name,description,properties in (
                ('init_machine','Collect this machine network settings and cached neighbors. No active discovery.',{}),
                ('find_ceh_tools','Find verified tool paths in the user-configured CEH tools index.',{'query':{'type':'string'}}),
                ('save_finding','Save only a confirmed flag and how it was found, using command or user evidence.',{'flag':{'type':'string'},'how_found':{'type':'string'}})):
                schema={'name':name,'description':description}
                if properties:schema['parameters']={'type':'object','properties':properties,'required':list(properties)}
                functions.append({'type':'function','function':schema})
        yield from complete(handler.client,prepared,model,functions,execute_command,show_outputs=cfg.get('SHOW_FUNCTIONS_OUTPUT')=='true',actions=actions,history=messages)
    handler.Handler.get_completion=get_completion
    from sgpt.app import entry_point
    entry_point()


if __name__=='__main__':
    try:main()
    except Exception as exc:
        if isinstance(exc,ProviderBlocked):
            print(str(exc),file=sys.stderr);sys.exit(2)
        # Provider error bodies can echo submitted data. Never print them/keys.
        print(f'Exam ShellGPT failed: {type(exc).__name__}; HTTP {getattr(exc,"status_code","n/a")}. Check endpoint, model, key and billing.',file=sys.stderr)
        if isinstance(exc,(AttributeError,TypeError,NameError)):
            import traceback
            frames=traceback.extract_tb(exc.__traceback__)
            for frame in frames[-4:]:print(f'Local diagnostic: {Path(frame.filename).name}:{frame.lineno} ({frame.name})',file=sys.stderr)
        sys.exit(1)
