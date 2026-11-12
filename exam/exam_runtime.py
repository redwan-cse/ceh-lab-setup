"""ShellGPT exam entry point; retains complete Gemini tool-call metadata."""
import json
import os
from pathlib import Path
import sys


def complete(client, messages, model, tools, execute, limit=8, show_outputs=True):
    for _ in range(limit):
        kwargs=dict(model=model,messages=messages,reasoning_effort='high',stream=False)
        if tools: kwargs.update(tools=tools,tool_choice='auto')
        response=client.chat.completions.create(**kwargs)
        message=response.choices[0].message.model_dump(exclude_none=True)
        calls=message.get('tool_calls',[])
        if message.get('content'): yield message['content']
        if not calls:return
        if not tools:raise RuntimeError('Unexpected tool call with tools disabled')
        messages.append(message)  # Includes Google thought signatures/extra_content.
        for call in calls:
            if call['function']['name']!='execute_shell_command':raise RuntimeError('Unknown tool refused')
            arguments=json.loads(call['function']['arguments'])
            if set(arguments)!={'shell_command'} or not isinstance(arguments['shell_command'],str):raise RuntimeError('Invalid tool arguments')
            result=execute(arguments['shell_command'])
            if show_outputs:yield '\n```text\n'+result+'\n```\n'
            messages.append(dict(role='tool',tool_call_id=call['id'],content=result))
    raise RuntimeError('Tool continuation limit reached; request stopped')


def main():
    path=Path.home()/'.config'/'shell_gpt_exam'/'.sgptrc'
    values=dict(line.split('=',1) for line in path.read_text(encoding='utf-8').splitlines() if '=' in line and not line.startswith('#'))
    # Provider/function overrides must not bypass the protected exam config.
    for name in values:os.environ.pop(name,None)
    if not values.get('OPENAI_API_KEY'):
        if any(x in sys.argv for x in ('--version','--help')):os.environ['OPENAI_API_KEY']='offline-version-check'
        else:raise RuntimeError('Save your Gemini key using setup_exam.py --key-only')
    import sgpt.handlers.handler as handler
    from sgpt.config import cfg
    if os.name=='nt':from sgpt.shellgpt_command_guard import execute_command
    else:from sgpt.linux_command_guard import execute_command
    def get_completion(self,model,temperature,top_p,messages,functions=None,caching=False,**kwargs):
        if self.role.name in ('shell','code','describe_shell'):functions=None
        yield from complete(handler.client,messages,model,functions,execute_command,show_outputs=cfg.get('SHOW_FUNCTIONS_OUTPUT')=='true')
    handler.Handler.get_completion=get_completion
    from sgpt.app import entry_point
    entry_point()


if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Provider error bodies can echo submitted data. Never print them/keys.
        print(f'Exam ShellGPT failed: {type(exc).__name__}; HTTP {getattr(exc,"status_code","n/a")}. Check endpoint, model, key and billing.',file=sys.stderr)
        sys.exit(1)
