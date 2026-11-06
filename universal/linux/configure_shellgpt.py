"""Configure a pinned venv installation. Retains an existing API key."""
import importlib.metadata
import os
from pathlib import Path
import pwd
import shutil
import sys
import sysconfig
from urllib.parse import urlsplit


def preserved_stepfun_key(existing):
    """Never forward a key saved for a foreign provider to StepFun."""
    try:
        provider = urlsplit(existing.get('API_BASE_URL', ''))
        recognized = (provider.scheme == 'https' and provider.hostname == 'api.stepfun.ai'
                      and provider.port in (None, 443) and provider.username is None
                      and provider.password is None)
    except ValueError:
        recognized = False
    return existing.get('OPENAI_API_KEY', '') if recognized else ''

if sys.prefix == sys.base_prefix:
    raise SystemExit('Use setup-shellgpt-parrot.sh; a dedicated venv is required.')
if importlib.metadata.version('shell-gpt') != '1.5.1':
    raise SystemExit('Expected ShellGPT 1.5.1')
resources = Path(__file__).resolve().parent
home = Path.home()
config = home / '.config' / 'shell_gpt'
if config.is_symlink():
    raise SystemExit('Refusing a redirected ShellGPT config directory.')
config.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(config, 0o700)
config_file = config / '.sgptrc'
if config_file.is_symlink():
    raise SystemExit('Refusing a redirected API-key config file.')
existing = {}
if config_file.exists():
    for line in config_file.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            name, value = line.split('=', 1)
            existing[name] = value
saved_key = preserved_stepfun_key(existing)
if existing.get('OPENAI_API_KEY') and not saved_key:
    print('Existing provider is not recognized as StepFun; OPENAI_API_KEY will be left empty. Configure a StepFun key explicitly.')
settings = {
    'OPENAI_API_KEY': saved_key,
    'DEFAULT_MODEL': 'step-5-preview',
    'API_BASE_URL': 'https://api.stepfun.ai/step_plan/v1',
    'REASONING_EFFORT': 'high',
    'USE_LITELLM': 'false',
    'OPENAI_USE_FUNCTIONS': 'true',
    'OPENAI_FUNCTIONS_PATH': str(config / 'functions-stepfun'),
    'ROLE_STORAGE_PATH': str(config / 'roles-stepfun'),
    'SHELL_NAME': 'bash',
    'SHELL_INTERACTION': 'true',
    'REQUEST_TIMEOUT': '300',
    'CACHE_PATH': str(config / 'cache-stepfun'),
    'CHAT_CACHE_PATH': str(config / 'chat-cache-stepfun'),
}
config_file.write_text(''.join(f'{key}={value}\n' for key, value in settings.items()), encoding='utf-8')
os.chmod(config_file, 0o600)
package = Path(sysconfig.get_path('purelib')) / 'sgpt'
shutil.copyfile(resources / 'linux_command_guard.py', package / 'linux_command_guard.py')


def patch(filename, replacements):
    path = package / filename
    source = path.read_text(encoding='utf-8')
    for before, after in replacements:
        if source.count(before) != 1:
            raise RuntimeError(f'Unexpected ShellGPT source: {filename}; refusing to patch')
        source = source.replace(before, after)
    compile(source, str(path), 'exec')
    path.write_text(source, encoding='utf-8')


patch('handlers/handler.py', (
    ('    additional_kwargs = {}\n', '    additional_kwargs = {"reasoning_effort": cfg.get("REASONING_EFFORT")}\n'),
    ('        arguments: str,\n', '        arguments: str,\n        reasoning_content: str = "",\n'),
    ('                "content": None,\n', '                "content": None,\n                "reasoning_content": reasoning_content,\n'),
    ('        tool_call_id = name = arguments = ""\n', '        tool_call_id = name = arguments = ""\n        reasoning_content = ""\n'),
    ('                delta = chunk.choices[0].delta\n', '                delta = chunk.choices[0].delta\n                reasoning_content += getattr(delta, "reasoning_content", None) or ""\n'),
    ('                        messages, tool_call_id, name, arguments\n', '                        messages, tool_call_id, name, arguments, reasoning_content\n'),
))
utils = package / 'utils.py'
source = utils.read_text(encoding='utf-8')
start = source.index('def run_command(command: str) -> None:')
end = source.index('\n\ndef option_callback', start)
source = source[:start] + 'def run_command(command: str) -> None:\n    from sgpt.linux_command_guard import run_command as guarded_run\n    guarded_run(command)\n' + source[end:]
compile(source, str(utils), 'exec')
utils.write_text(source, encoding='utf-8')
app = package / 'app.py'
source = app.read_text(encoding='utf-8')
start = source.index('    session: PromptSession[str] = PromptSession()')
end = source.index('\n\ndef entry_point()', start)
source = source[:start] + '    if shell and interaction:\n        run_command(full_completion)\n' + source[end:]
compile(source, str(app), 'exec')
app.write_text(source, encoding='utf-8')
function_source = '''from pydantic import BaseModel, Field
from sgpt.linux_command_guard import execute_command

class Function(BaseModel):
    """Execute a Linux command. Recognized inspection runs automatically;
    other commands require approval. Respect refusal and never bypass it."""
    shell_command: str = Field(..., description="Linux shell command to execute")

    @classmethod
    def execute(cls, shell_command: str) -> str:
        return execute_command(shell_command)

    @classmethod
    def openai_schema(cls):
        schema = cls.model_json_schema()
        return {"type":"function", "function":{
            "name":"execute_shell_command", "description":cls.__doc__.strip(),
            "parameters":{"type":"object", "properties":schema["properties"], "required":schema["required"]}}}
'''
functions = Path(settings['OPENAI_FUNCTIONS_PATH'])
functions.mkdir(exist_ok=True, mode=0o700)
for other in functions.glob('*.py'):
    if other.name != 'execute_shell.py':
        raise RuntimeError(f'Unexpected custom tool in the guarded function directory: {other.name}')
(functions / 'execute_shell.py').write_text(function_source, encoding='utf-8')
(package / 'llm_functions' / 'common' / 'execute_shell.py').write_text(function_source, encoding='utf-8')

# An explicit wrapper avoids Debian's externally-managed system Python and
# inherited provider/function-path environment values overriding this setup.
venv_python = Path(sys.executable)
wrapper = home / '.local' / 'bin' / 'sgpt'
if wrapper.is_symlink():
    raise SystemExit('Existing ~/.local/bin/sgpt is a symlink; review it before replacement.')
import shlex
clear_names = ' '.join(settings)
wrapper.write_text('#!/bin/sh\n' + 'unset ' + clear_names + '\n' +
                   'export PYTHONIOENCODING=utf-8\n' +
                   'exec ' + shlex.quote(str(venv_python)) + ' -m sgpt "$@"\n', encoding='utf-8')
os.chmod(wrapper, 0o700)
marker = '# ShellGPT StepFun user command path'
path_line = 'case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH" ;; esac\n'
shell = Path(pwd.getpwuid(os.getuid()).pw_shell).name
dotfiles = [home / '.profile', home / ('.zshenv' if shell == 'zsh' else '.bashrc')]
for dotfile in dotfiles:
    if dotfile.is_symlink():
        raise SystemExit(f'Refusing a redirected shell startup file: {dotfile.name}')
    text = dotfile.read_text(encoding='utf-8') if dotfile.exists() else ''
    if marker not in text:
        dotfile.write_text(marker + '\n' + path_line + text, encoding='utf-8')
print('Configured StepFun high reasoning and guarded Bash execution.')
print(f'API key file: {config_file} (mode 600)')
