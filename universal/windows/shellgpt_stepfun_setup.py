"""Companion to Setup-ShellGPT-StepFun.ps1. No API keys belong in this file."""
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import winreg

VERSION = '1.5.1'
assert sys.version_info >= (3, 10), 'Python 3.10+ required'
resources = Path(__file__).resolve().parent
for resource in ('shellgpt_command_guard.py', 'shellgpt_command_policy.ps1', 'test_command_guard.py'):
    if not (resources / resource).is_file():
        raise RuntimeError(f'Missing setup resource: {resource}')
isolated = '--isolated-child' in sys.argv
if '--isolated-test' in sys.argv:
    test_root = Path(tempfile.mkdtemp(prefix='sgpt-setup-test-'))
    environment = os.environ.copy()
    environment.update(USERPROFILE=str(test_root / 'profile'), APPDATA=str(test_root / 'roaming'),
                       PYTHONUSERBASE=str(test_root / 'python-user'), SGPT_ISOLATED_ROOT=str(test_root))
    for folder in ('profile', 'roaming', 'python-user'):
        (test_root / folder).mkdir()
    print(f'Isolated test files: {test_root}', flush=True)
    subprocess.run([sys.executable, str(Path(__file__).resolve()), '--isolated-child'], env=environment, check=True)
    sys.exit(0)
if isolated:
    test_root = Path(os.environ['SGPT_ISOLATED_ROOT']).resolve()
    assert Path.home().resolve().is_relative_to(test_root)
    assert Path(sysconfig.get_path('purelib', 'nt_user')).resolve().is_relative_to(test_root)
home = Path.home().resolve()
config = home / '.config' / 'shell_gpt'
# Preserve only the existing key; the supported provider and guard configuration
# are regenerated on every reinstall. Never inspect or delete generic temp caches.
def read_saved_key(config_file, reset=False):
    """Return (key, foreign_provider_key_discarded), without exposing values."""
    from urllib.parse import urlsplit
    if reset or not config_file.exists():
        return '', False
    values = {}
    for line in config_file.read_text(encoding='utf-8-sig').splitlines():
        name, separator, value = line.partition('=')
        if separator:
            values[name] = value
    key = values.get('OPENAI_API_KEY', '')
    if not key:
        return '', False
    try:
        provider = urlsplit(values.get('API_BASE_URL', ''))
        recognized = (provider.scheme == 'https' and provider.hostname == 'api.stepfun.ai'
                      and provider.port in (None, 443) and not provider.username and not provider.password)
    except ValueError:
        recognized = False
    return (key, False) if recognized else ('', True)


def check_environment_conflicts(names, *environments):
    """Reject overriding settings while returning no credential values."""
    conflicts = sorted({name for environment in environments for name in names if environment.get(name)})
    if conflicts:
        raise RuntimeError('Environment settings override ShellGPT configuration: ' + ', '.join(conflicts)
                           + '. Review/unset those values for this Windows account, then open a new terminal and rerun. No persistent environment values were changed.')


config_file = config / '.sgptrc'
preserved_key, discarded_foreign_key = read_saved_key(config_file, '--reset-config' in sys.argv)
if discarded_foreign_key:
    print('Existing OPENAI_API_KEY was not preserved because API_BASE_URL is not a recognized StepFun HTTPS provider. Use -PromptForApiKey locally to enter a StepFun key.', flush=True)

# Environment settings override ShellGPT's file. Fail before uninstalling or
# deleting anything, and leave persistent credentials belonging to other apps alone.
names = ('OPENAI_API_KEY', 'API_BASE_URL', 'DEFAULT_MODEL', 'REASONING_EFFORT',
         'USE_LITELLM', 'OPENAI_USE_FUNCTIONS', 'OPENAI_FUNCTIONS_PATH',
         'ROLE_STORAGE_PATH', 'SHELL_NAME', 'SHELL_INTERACTION', 'CACHE_PATH', 'CHAT_CACHE_PATH')
if not isolated:
    persistent_environment = {}
    for hive, location in ((winreg.HKEY_CURRENT_USER, 'Environment'),
                           (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')):
        try:
            with winreg.OpenKey(hive, location) as env:
                for name in names:
                    try:
                        value, _ = winreg.QueryValueEx(env, name)
                        if value:
                            persistent_environment[name] = value
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
    check_environment_conflicts(names, os.environ, persistent_environment)
for name in names:
    os.environ.pop(name, None)

def run(*args):
    subprocess.run(args, check=True)

def remove_owned(path, root, names):
    if not path.exists():
        return
    resolved = path.resolve()
    assert resolved.parent == root and resolved.name in names, f'Unsafe removal path: {path}'
    assert not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(), f'Reparse point: {path}'
    shutil.rmtree(path)

print('Reinstalling ShellGPT; regenerating its owned configuration (recognized StepFun key preserved unless reset)...', flush=True)
if not isolated:
    run(sys.executable, '-m', 'pip', 'uninstall', '-y', 'shell-gpt')
remove_owned(config, home / '.config', {'shell_gpt'})

install_flag = '--ignore-installed' if isolated else '--force-reinstall'
run(sys.executable, '-m', 'pip', 'install', '--user', '--no-cache-dir', install_flag, '--no-deps', f'shell-gpt=={VERSION}')
# ShellGPT imports Click directly and expects the Click-based Typer API.
# Pin compatible CLI dependencies instead of inheriting future Typer changes.
dependency_flags = ['--ignore-installed'] if isolated else []
run(sys.executable, '-m', 'pip', 'install', '--user', *dependency_flags, f'shell-gpt=={VERSION}',
    'typer==0.16.0', 'click==8.1.8')
# Python omits a user site directory that did not exist at interpreter startup.
sys.path.insert(0, sysconfig.get_path('purelib', 'nt_user'))
import importlib
importlib.invalidate_caches()
config.mkdir(parents=True)
settings = {
    'OPENAI_API_KEY': preserved_key,
    'DEFAULT_MODEL': 'step-5-preview',
    'API_BASE_URL': 'https://api.stepfun.ai/step_plan/v1',
    'REASONING_EFFORT': 'high',
    'USE_LITELLM': 'false',
    'OPENAI_USE_FUNCTIONS': 'true',
    'OPENAI_FUNCTIONS_PATH': str(config / 'functions'),
    'ROLE_STORAGE_PATH': str(config / 'roles'),
    'SHELL_NAME': 'powershell.exe',
    'SHELL_INTERACTION': 'true',
    'REQUEST_TIMEOUT': '300',
    'CACHE_PATH': str(config / 'cache'),
    'CHAT_CACHE_PATH': str(config / 'chat_cache'),
}
config_file = config / '.sgptrc'
config_file.write_text(''.join(f'{k}={v}\n' for k, v in settings.items()), encoding='utf-8')
identity = subprocess.check_output(['whoami'], text=True).strip()
run('icacls', str(config), '/inheritance:r', '/grant:r', f'{identity}:(OI)(CI)F', 'SYSTEM:(OI)(CI)F')
run('icacls', str(config_file), '/inheritance:r', '/grant:r', f'{identity}:F', 'SYSTEM:F')

# ShellGPT 1.5.1 does not forward reasoning effort itself. Pin the release
# and fail closed if its request source no longer matches the expected code.
assert importlib.metadata.version('shell-gpt') == VERSION
package = Path(sysconfig.get_path('purelib', 'nt_user')) / 'sgpt'
handler_file = package / 'handlers' / 'handler.py'
source = handler_file.read_text(encoding='utf-8')
needle = '    additional_kwargs = {}\n'
replacement = '    additional_kwargs = {"reasoning_effort": cfg.get("REASONING_EFFORT")}\n'
assert source.count(needle) == 1, 'Unexpected source; refusing compatibility patch'
source = source.replace(needle, replacement)
# Preserve streamed reasoning on assistant tool-call messages, as required by
# the StepFun continuation protocol. Each replacement is checked for drift.
protocol_patches = (
    ('        arguments: str,\n', '        arguments: str,\n        reasoning_content: str = "",\n'),
    ('                "content": None,\n', '                "content": None,\n                "reasoning_content": reasoning_content,\n'),
    ('        tool_call_id = name = arguments = ""\n', '        tool_call_id = name = arguments = ""\n        reasoning_content = ""\n'),
    ('                delta = chunk.choices[0].delta\n',
     '                delta = chunk.choices[0].delta\n                reasoning_content += getattr(delta, "reasoning_content", None) or ""\n'),
    ('                        messages, tool_call_id, name, arguments\n',
     '                        messages, tool_call_id, name, arguments, reasoning_content\n'),
)
for before, after in protocol_patches:
    assert source.count(before) == 1, 'Unexpected tool handler; refusing protocol patch'
    source = source.replace(before, after)
handler_file.write_text(source, encoding='utf-8')
compile(handler_file.read_text(encoding='utf-8'), str(handler_file), 'exec')

# Install one guarded execution function and guard the --shell path too.
for filename in ('shellgpt_command_guard.py', 'shellgpt_command_policy.ps1'):
    shutil.copyfile(resources / filename, package / filename)
function_source = '''from typing import Any, Dict
from pydantic import BaseModel, Field
from sgpt.shellgpt_command_guard import execute_command

class Function(BaseModel):
    """Execute a PowerShell command. Inspection commands run automatically;
    other commands require the user's approval. Respect refusal and do not
    attempt alternate commands to bypass it."""
    shell_command: str = Field(..., description="PowerShell command to execute")

    @classmethod
    def execute(cls, shell_command: str) -> str:
        return execute_command(shell_command)

    @classmethod
    def openai_schema(cls) -> Dict[str, Any]:
        schema = cls.model_json_schema()
        return {"type":"function", "function":{
            "name":"execute_shell_command", "description":cls.__doc__.strip(),
            "parameters":{"type":"object", "properties":schema["properties"], "required":schema["required"]}}}
'''
functions = config / 'functions'
functions.mkdir()
(functions / 'execute_shell.py').write_text(function_source, encoding='utf-8')
# Keep --install-functions from reinstalling the unguarded upstream runner.
(package / 'llm_functions' / 'common' / 'execute_shell.py').write_text(function_source, encoding='utf-8')
utils_file = package / 'utils.py'
source = utils_file.read_text(encoding='utf-8')
start = source.index('def run_command(command: str) -> None:')
end = source.index('\n\ndef option_callback', start)
source = source[:start] + 'def run_command(command: str) -> None:\n    from sgpt.shellgpt_command_guard import run_command as guarded_run\n    guarded_run(command)\n' + source[end:]
utils_file.write_text(source, encoding='utf-8')
app_file = package / 'app.py'
source = app_file.read_text(encoding='utf-8')
start = source.index('    session: PromptSession[str] = PromptSession()')
end = source.index('\n\ndef entry_point()', start)
source = source[:start] + '    if shell and interaction:\n        run_command(full_completion)\n' + source[end:]
app_file.write_text(source, encoding='utf-8')
for filename in (utils_file, app_file, functions / 'execute_shell.py'):
    compile(filename.read_text(encoding='utf-8'), str(filename), 'exec')

# Exercise the actual request builder with an HTTP mock. No network request
# or real credential is used for this verification.
os.environ['OPENAI_API_KEY'] = 'offline-verification-only'
import httpx
from types import SimpleNamespace
from openai import OpenAI
from sgpt.config import cfg
from sgpt.handlers import handler as module
captured = {}
def respond(request):
    assert str(request.url) == settings['API_BASE_URL'] + '/chat/completions'
    captured.update(json.loads(request.content))
    event = {'id':'offline','object':'chat.completion.chunk','created':0,'model':'step-5-preview','choices':[{'index':0,'delta':{'content':'OK'},'finish_reason':'stop'}]}
    return httpx.Response(200, headers={'content-type':'text/event-stream'}, text='data: ' + json.dumps(event) + '\n\ndata: [DONE]\n\n')
client = OpenAI(api_key='offline-verification-only', base_url=cfg.get('API_BASE_URL'), max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(respond)))
module.completion = client.chat.completions.create
handler = module.Handler.__new__(module.Handler)
handler.role = SimpleNamespace(name='verification')
result = ''.join(handler.get_completion(model=cfg.get('DEFAULT_MODEL'), temperature=0.1, top_p=1.0, messages=[{'role':'user','content':'Reply OK'}], functions=None, caching=False))
assert result == 'OK'
assert captured['model'] == 'step-5-preview'
assert captured['reasoning_effort'] == 'high'
assert captured['stream'] is True
assert cfg.get('OPENAI_USE_FUNCTIONS') == 'true'
assert cfg.get('OPENAI_API_KEY') == 'offline-verification-only'
print('PASS: StepFun endpoint, model, high reasoning effort and streaming verified offline.')
print(f'API key location: {config_file}')
run(sys.executable, '-m', 'unittest', 'discover', '-s', str(resources), '-v')
run(str(Path(sysconfig.get_path('scripts', 'nt_user')) / 'sgpt.exe'), '--version')
# Verify the installed paths use the guard, without a live API call.
from unittest.mock import patch
from sgpt import app, utils
from sgpt.function import get_function, get_openai_schemas
from sgpt import shellgpt_command_guard as installed_guard
assert len(get_openai_schemas()) == 1
assert 'run_command(full_completion)' in app_file.read_text(encoding='utf-8')
with patch('builtins.input', side_effect=AssertionError('Unexpected approval prompt')):
    result = get_function('execute_shell_command')('Get-Location')
    assert 'Exit code: 0' in result
    utils.run_command('Get-Date')
with patch('builtins.input', return_value='no'):
    assert 'not executed' in get_function('execute_shell_command')('Remove-Item nonexistent-test-target')
    utils.run_command('winget install nonexistent-test-package')
print('PASS: installed tool and shell runner both enforce the command guard.')

# Exercise the actual CLI path without a Windows console. The replaced shell
# menu no longer needs upstream's unconditional PromptSession construction.
import typer
from typer.testing import CliRunner
application = typer.Typer()
application.command()(app.main)
runner = CliRunner()
with patch.object(app.DefaultHandler, 'handle', return_value='Get-Location'):
    with patch('builtins.input', side_effect=AssertionError('Unexpected approval prompt')):
        cli_result = runner.invoke(application, ['--shell', '--no-functions', 'Inspect current location'])
assert cli_result.exit_code == 0, repr(cli_result.exception) + cli_result.output
assert 'Automatically running' in cli_result.output and 'Exit code: 0' in cli_result.output
with patch.object(app.DefaultHandler, 'handle', return_value='Remove-Item nonexistent-cli-test-target'):
    with patch('builtins.input', return_value='no'):
        cli_result = runner.invoke(application, ['--shell', '--no-functions', 'Test refusal'])
assert cli_result.exit_code == 0, repr(cli_result.exception) + cli_result.output
assert 'not executed' in cli_result.output
print('PASS: real CLI shell routing automatically inspects and refuses unapproved deletion.')

# Simulate a complete streaming tool call and continuation. The assistant's
# reasoning_content must survive into StepFun's subsequent request.
requests = []
def respond_tool(request):
    body = json.loads(request.content)
    requests.append(body)
    assert body['reasoning_effort'] == 'high'
    assert body['tools'][0]['function']['name'] == 'execute_shell_command'
    if len(requests) == 1:
        delta = {'reasoning_content':'offline-protocol-test', 'tool_calls':[{
            'index':0, 'id':'call_offline', 'type':'function',
            'function':{'name':'execute_shell_command', 'arguments':json.dumps({'shell_command':'Get-Location'})}}]}
        finish = 'tool_calls'
    else:
        assert len(requests) == 2
        assistant = body['messages'][-2]
        assert assistant['reasoning_content'] == 'offline-protocol-test'
        assert assistant['tool_calls'][0]['id'] == 'call_offline'
        assert body['messages'][-1]['tool_call_id'] == 'call_offline'
        assert 'Exit code: 0' in body['messages'][-1]['content']
        delta, finish = {'content':'tool-complete'}, 'stop'
    event = {'id':'offline', 'object':'chat.completion.chunk','created':0,'model':'step-5-preview',
             'choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
    return httpx.Response(200, headers={'content-type':'text/event-stream'},
                          text='data: ' + json.dumps(event) + '\n\ndata: [DONE]\n\n')
tool_client = OpenAI(api_key='offline-verification-only', base_url=cfg.get('API_BASE_URL'), max_retries=0,
                    http_client=httpx.Client(transport=httpx.MockTransport(respond_tool)))
module.completion = tool_client.chat.completions.create
tool_output = ''.join(handler.get_completion(model=cfg.get('DEFAULT_MODEL'), temperature=0.1, top_p=1.0,
                     messages=[{'role':'user','content':'Inspect the current directory'}],
                     functions=get_openai_schemas(), caching=False))
assert 'tool-complete' in tool_output
assert len(requests) == 2
print('PASS: streaming tool execution and StepFun reasoning continuation verified offline.')
