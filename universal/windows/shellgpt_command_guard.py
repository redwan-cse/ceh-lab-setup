"""Selective approval for ShellGPT on Windows. This is not an OS sandbox."""
import base64
import json
from pathlib import Path
import subprocess


def powershell():
    # Do not resolve powershell.exe through the current directory or PATH.
    import ctypes
    buffer = ctypes.create_unicode_buffer(32768)
    if not ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer)):
        raise RuntimeError('Cannot locate system PowerShell')
    return str(Path(buffer.value) / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe')


def classify(command):
    encoded = base64.b64encode(command.encode('utf-8')).decode('ascii')
    result = subprocess.run(
        [powershell(), '-NoLogo', '-NoProfile', '-NonInteractive',
         '-ExecutionPolicy', 'Bypass', '-File',
         str(Path(__file__).with_name('shellgpt_command_policy.ps1')),
         '-CommandBase64', encoded],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
    )
    if result.returncode:
        raise RuntimeError('Command policy failed')
    decision = json.loads(result.stdout.strip().lstrip('\ufeff'))
    if type(decision.get('automatic')) is not bool:
        raise RuntimeError('Invalid command policy response')
    return decision


def execute_command(command):
    try:
        decision = classify(command)
    except Exception:
        return 'Command not executed: approval policy could not be evaluated.'
    if decision['automatic']:
        # Import qualified cmdlets only from system modules in a fresh session.
        code = '$env:PSModulePath = Join-Path $PSHOME "Modules"; ' + decision['command']
        print('[sgpt] Automatically running recognized inspection command:\n' + command, flush=True)
    else:
        # Escape control characters so an unknown command cannot hide itself
        # using terminal cursor/erase sequences in the approval display.
        print('[sgpt] Approval required: ' + decision['reason'] + '\n' + json.dumps(command, ensure_ascii=False), flush=True)
        try:
            approved = input('Execute this exact command? Type yes to approve: ').strip().lower() == 'yes'
        except (EOFError, KeyboardInterrupt, OSError):
            approved = False
        if not approved:
            return 'Command not executed: approval was not given.'
        code = command
    # Avoid PowerShell serializing module-loading progress as CLIXML into the
    # command output returned to the model and printed in the terminal.
    code = "$ProgressPreference = 'SilentlyContinue'; " + code
    encoded = base64.b64encode(code.encode('utf-16le')).decode('ascii')
    try:
        result = subprocess.run(
            [powershell(), '-NoLogo', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
            capture_output=True, text=True, errors='replace', timeout=300,
        )
        return f'Exit code: {result.returncode}, Output:\n{result.stdout}{result.stderr}'
    except subprocess.TimeoutExpired:
        return 'Command timed out after 300 seconds; check for any child processes still running.'
    except OSError as error:
        return f'Command could not start: {error}'


def run_command(command):
    print(execute_command(command))
