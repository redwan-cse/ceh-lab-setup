"""Prompt locally without putting credentials in arguments, output or history."""
import getpass
import os
from pathlib import Path
import sys
import tempfile


def save_key(path: Path, key: str) -> bool:
    if not key:
        return False
    if '\r' in key or '\n' in key:
        raise ValueError('API key must be one line.')
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Refusing a redirected configuration path.')
    lines = path.read_text(encoding='utf-8').splitlines()
    settings = dict(line.split('=', 1) for line in lines
                    if '=' in line and not line.startswith('#'))
    if settings.get('API_BASE_URL') != 'https://api.stepfun.ai/step_plan/v1':
        raise ValueError('Run the StepFun installer before configuring its key.')
    updated = [line for line in lines if not line.startswith('OPENAI_API_KEY=')]
    updated.insert(0, 'OPENAI_API_KEY=' + key)
    descriptor, name = tempfile.mkstemp(prefix='.sgptrc-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write('\n'.join(updated) + '\n')
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return True


def main():
    if not sys.stdin.isatty():
        print('No interactive terminal: configure the API key later using prompt_api_key.py.')
        return
    path = Path.home() / '.config' / 'shell_gpt' / '.sgptrc'
    key = getpass.getpass('StepFun API key (hidden; Enter keeps the saved key): ')
    changed = save_key(path, key)
    print('API key saved (mode 600).' if changed else 'Saved API key unchanged.')


if __name__ == '__main__':
    main()
