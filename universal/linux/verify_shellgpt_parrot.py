"""Offline verification by default; --live makes three small API requests."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch


def offline():
    # Dummy key stays in this verification process; never written to config.
    os.environ['OPENAI_API_KEY'] = 'offline-verification-only'
    import httpx
    from openai import OpenAI
    from sgpt.config import cfg
    from sgpt.function import get_function, get_openai_schemas
    from sgpt.handlers import handler as module
    from sgpt import app
    import typer
    from typer.testing import CliRunner
    assert cfg.get('DEFAULT_MODEL') == 'step-5-preview'
    assert cfg.get('API_BASE_URL') == 'https://api.stepfun.ai/step_plan/v1'
    assert cfg.get('REASONING_EFFORT') == 'high'
    assert len(get_openai_schemas()) == 1
    requests = []
    def respond(request):
        assert str(request.url) == 'https://api.stepfun.ai/step_plan/v1/chat/completions'
        body = json.loads(request.content)
        requests.append(body)
        assert body['model'] == 'step-5-preview' and body['reasoning_effort'] == 'high'
        assert body['stream'] is True
        if len(requests) == 1:
            delta = {'reasoning_content':'offline-test', 'tool_calls':[{
                'index':0,'id':'call_test','type':'function','function':{
                    'name':'execute_shell_command','arguments':json.dumps({'shell_command':'pwd'})}}]}
            finish = 'tool_calls'
        else:
            assert len(requests) == 2
            assert body['messages'][-2]['reasoning_content'] == 'offline-test'
            assert body['messages'][-1]['tool_call_id'] == 'call_test'
            assert 'Exit code: 0' in body['messages'][-1]['content']
            delta, finish = {'content':'OK'}, 'stop'
        event = {'id':'offline','object':'chat.completion.chunk','created':0,'model':'step-5-preview',
                 'choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
        return httpx.Response(200, headers={'content-type':'text/event-stream'},
                              text='data: '+json.dumps(event)+'\n\ndata: [DONE]\n\n')
    client = OpenAI(api_key='offline-verification-only', base_url=cfg.get('API_BASE_URL'), max_retries=0,
                    http_client=httpx.Client(transport=httpx.MockTransport(respond)))
    module.completion = client.chat.completions.create
    handler = module.Handler.__new__(module.Handler)
    handler.role = SimpleNamespace(name='verification')
    output = ''.join(handler.get_completion(model=cfg.get('DEFAULT_MODEL'), temperature=0.1, top_p=1,
                     messages=[{'role':'user','content':'Inspect directory'}], functions=get_openai_schemas(), caching=False))
    assert 'OK' in output and len(requests) == 2
    application = typer.Typer()
    application.command()(app.main)
    runner = CliRunner()
    with patch.object(app.DefaultHandler, 'handle', return_value='pwd'):
        with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
            result = runner.invoke(application, ['--shell','--no-functions','inspect'])
    assert result.exit_code == 0, repr(result.exception) + result.output
    assert 'Automatically running' in result.output and 'Exit code: 0' in result.output
    with patch('builtins.input', return_value='no'):
        assert 'not executed' in get_function('execute_shell_command')('rm nonexistent-test-target')
    print('PASS: offline endpoint/model/high effort, streaming tool continuation, CLI execution and refusal.')


def live():
    config = Path.home() / '.config' / 'shell_gpt' / '.sgptrc'
    settings = dict(line.split('=',1) for line in config.read_text(encoding='utf-8').splitlines()
                    if '=' in line and not line.startswith('#'))
    key = settings.get('OPENAI_API_KEY', '')
    if not key:
        raise SystemExit(f'Save OPENAI_API_KEY in {config} first.')
    cli = str(Path.home() / '.local' / 'bin' / 'sgpt')
    environment = os.environ.copy()
    environment['SHOW_FUNCTIONS_OUTPUT'] = 'true'
    checks = (
        (['--no-cache','--no-functions','Reply with exactly SGPT_PARROT_OK'], ['SGPT_PARROT_OK']),
        (['--shell','--no-cache','--no-functions','Return exactly the Bash command pwd and nothing else'],
            ['Automatically running','pwd','Exit code: 0']),
        (['--no-cache','Use execute_shell_command exactly once to run date. After it succeeds, reply with exactly SGPT_TOOL_OK. Do not run other commands.'],
            ['Automatically running','date','Exit code: 0','SGPT_TOOL_OK']),
    )
    for number, (arguments, expected) in enumerate(checks, 1):
        print(f'Live test {number}...', flush=True)
        result = subprocess.run([cli,*arguments], input='', capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=240, env=environment)
        output = (result.stdout + result.stderr).replace(key, '[REDACTED]')
        print(output, flush=True)
        if result.returncode or 'Approval required' in output or any(token not in output for token in expected):
            raise SystemExit(f'FAIL: live test {number}, exit {result.returncode}')
        print(f'PASS: live test {number}', flush=True)
    print('PASS: live StepFun text, automatic Bash execution and tool continuation.')


if __name__ == '__main__':
    if '--live' in sys.argv:
        live()
    else:
        offline()
