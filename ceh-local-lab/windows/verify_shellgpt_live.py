"""Run after setup and saving a StepFun key. Uses small, billable API requests.

Usage on the target Windows PC: python verify_shellgpt_live.py
Tests plain completion, automatic --shell execution, and a real guarded tool
round trip. No deletion or installation is performed. Never prints the API key.
"""
import os
from pathlib import Path
import subprocess
import sys


def main():
    # SSH/redirection on Windows may otherwise select cp1252, which cannot
    # print Unicode emitted by Rich or by the model's response.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    path = Path.home() / '.config' / 'shell_gpt' / '.sgptrc'
    settings = dict(line.split('=', 1) for line in path.read_text(encoding='utf-8').splitlines()
                    if line.strip() and not line.startswith('#'))
    key = os.environ.get('OPENAI_API_KEY') or settings.get('OPENAI_API_KEY', '')
    if not key:
        raise SystemExit(f'Save OPENAI_API_KEY in {path} before live verification.')
    from sgpt.config import cfg
    for name, expected in (
        ('DEFAULT_MODEL', 'step-5-preview'),
        ('API_BASE_URL', 'https://api.stepfun.ai/step_plan/v1'),
        ('REASONING_EFFORT', 'high'),
        ('OPENAI_USE_FUNCTIONS', 'true'),
    ):
        if cfg.get(name) != expected:
            raise SystemExit(f'Unexpected effective setting: {name}')
    environment = os.environ.copy()
    environment['SHOW_FUNCTIONS_OUTPUT'] = 'true'
    environment['PYTHONIOENCODING'] = 'utf-8'
    tests = (
        ('plain StepFun response', ['--no-cache', '--no-functions',
            'Reply with exactly SGPT_STEPFUN_LIVE_OK'], ['SGPT_STEPFUN_LIVE_OK']),
        ('automatic shell execution', ['--shell', '--no-cache', '--no-functions',
            'Return exactly this PowerShell command and nothing else: Get-Location'],
            ['Automatically running', 'Get-Location', 'Exit code: 0']),
        ('automatic tool round trip', ['--no-cache',
            'Use execute_shell_command exactly once to execute Get-Date. After it succeeds, '
            'reply with exactly SGPT_TOOL_OK. Do not execute or suggest any other commands.'],
            ['Automatically running', 'Get-Date', 'Exit code: 0', 'SGPT_TOOL_OK']),
    )
    for name, arguments, expected in tests:
        print(f'Testing {name}...', flush=True)
        result = subprocess.run([sys.executable, '-m', 'sgpt', *arguments], input='',
                                capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=240, env=environment)
        output = (result.stdout + result.stderr).replace(key, '[REDACTED]')
        print(output, flush=True)
        if result.returncode or 'Approval required' in output or any(token not in output for token in expected):
            raise SystemExit(f'FAIL: {name}; exit code {result.returncode}')
        print(f'PASS: {name}', flush=True)
    print('PASS: live StepFun responses and automatic command execution verified.')


if __name__ == '__main__':
    main()
