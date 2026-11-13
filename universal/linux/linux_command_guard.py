"""Selective approval for literal Linux inspection commands; not an OS sandbox."""
import contextlib
import json
import os
from pathlib import Path
import shlex
import signal
import stat
import subprocess
import tempfile
import time

READ_ONLY = {'pwd', 'ls', 'cat', 'head', 'tail', 'wc', 'id', 'whoami',
             'uname', 'ps', 'df', 'du', 'stat', 'readlink'}


def trusted_executable(name):
    if '/' in name and not name.startswith('/'):
        return None
    base = Path(name).name
    for directory in ('/usr/bin', '/bin', '/usr/sbin', '/sbin'):
        candidate = Path(directory) / base
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if '/' in name and Path(name).resolve() != resolved:
            continue
        if not os.access(resolved, os.X_OK):
            continue
        if any(item.stat().st_uid != 0 or item.stat().st_mode & (stat.S_IWGRP | stat.S_IWOTH)
               for item in (resolved, *resolved.parents)):
            continue
        return str(resolved)
    return None


def classify(command):
    deny = {'automatic': False, 'reason': 'Unknown command, script, installation or file-changing operation'}
    if not command.strip() or any(c in command for c in '\n\r;$`&><{}()'):
        return deny
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars='|')
        lexer.whitespace_split = True
        lexer.commenters = ''
        tokens = list(lexer)
    except ValueError:
        return deny
    segments = [[]]
    for token in tokens:
        if token and set(token) == {'|'} and token != '|':
            return deny
        if token == '|':
            if not segments[-1]:
                return deny
            segments.append([])
        else:
            segments[-1].append(token)
    if not segments[-1]:
        return deny
    pipeline = []
    for words in segments:
        name, args = Path(words[0]).name, words[1:]
        allowed = name in READ_ONLY
        if name == 'date':
            allowed = all(arg.startswith('+') or arg in ('-u', '--utc', '--universal') for arg in args)
        elif name == 'hostname':
            allowed = all(arg in ('-f', '-s', '-i', '-I', '-d', '-A', '--fqdn', '--short') for arg in args)
        elif name == 'ss':
            allowed = all(arg.startswith('-') and len(arg) > 1 and set(arg[1:]) <= set('tulnpas46') for arg in args)
        elif name == 'ip':
            allowed = len(args) >= 2 and args[0] in ('addr', 'address', 'link', 'route') and args[1] == 'show'
        elif name == 'sort':
            allowed = all(not arg.startswith('-') or arg in ('-n', '-r', '-u', '--numeric-sort', '--reverse', '--unique') for arg in args)
        elif name == 'systemctl':
            allowed = bool(args) and args[0] in ('status', 'is-active', 'is-enabled', 'list-units', 'show') and all(
                not arg.startswith('-') or arg in ('--no-pager', '--full') for arg in args[1:])
        executable = trusted_executable(words[0]) if allowed else None
        if not executable:
            return deny
        pipeline.append([executable, *args])
    return {'automatic': True, 'reason': 'Recognized literal inspection command', 'argv': pipeline}


def run_pipeline(pipeline,cwd=None,stdout_path=None,append=False,env=None):
    processes = []
    cleanup_groups = False
    deadline = time.monotonic() + 300
    with contextlib.ExitStack() as stack:
        error_files = []
        try:
            output_file=None
            if stdout_path:
                flags=os.O_WRONLY|os.O_CREAT|(os.O_APPEND if append else os.O_EXCL)|getattr(os,'O_NOFOLLOW',0)
                output_file=stack.enter_context(os.fdopen(os.open(stdout_path,flags,0o600),'ab' if append else 'wb'))
            previous = None
            for index,argv in enumerate(pipeline):
                error_file = stack.enter_context(tempfile.TemporaryFile())
                error_files.append(error_file)
                process = subprocess.Popen(argv, stdin=previous or subprocess.DEVNULL,
                                           stdout=output_file if output_file and index==len(pipeline)-1 else subprocess.PIPE, stderr=error_file,cwd=cwd,env=env,
                                           start_new_session=True)
                if previous is not None:
                    previous.close()
                previous = process.stdout
                processes.append(process)
            output, _ = processes[-1].communicate(timeout=max(0.1, deadline-time.monotonic()))
            for process in processes[:-1]:
                process.wait(timeout=max(0.1, deadline-time.monotonic()))
            errors = b''
            for error_file in error_files:
                error_file.seek(0)
                errors += error_file.read()
            suffix='\nPipeline exit codes: '+','.join(str(process.returncode) for process in processes) if len(processes)>1 else ''
            if stdout_path:suffix+='\nSaved output: '+str(stdout_path)
            return f'Exit code: {processes[-1].returncode}, Output:\n' + ((output or b'') + errors).decode('utf-8', errors='replace')+suffix
        except subprocess.TimeoutExpired:
            cleanup_groups = True
            return 'Command timed out after 300 seconds.'
        except OSError as error:
            cleanup_groups = True
            return f'Command could not start: {error}'
        except BaseException:
            cleanup_groups = True
            raise
        finally:
            for process in processes:
                # A shell can exit before its background child closes stdout.
                # The process group must still be terminated on timeout/error.
                if cleanup_groups or process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait()
                if process.stdout is not None:
                    process.stdout.close()


def execute_command(command,auto_approve=None):
    try:
        decision = classify(command)
    except Exception:
        return 'Command not executed: approval policy failed.'
    if decision['automatic']:
        print('[sgpt] Automatically running recognized inspection command:\n' + command, flush=True)
        return run_pipeline(decision['argv'])
    if auto_approve is not None and auto_approve(command):
        environment={key:value for key,value in os.environ.items() if key not in ('BASH_ENV','ENV','SHELLOPTS','BASHOPTS') and not key.startswith('BASH_FUNC_')}
        return run_pipeline([['/bin/bash','--noprofile','--norc','-c',command]],env=environment)
    print('[sgpt] Approval required: ' + decision['reason'] + '\n' + json.dumps(command), flush=True)
    try:
        approved = input('Execute this exact command? Type yes to approve: ').strip().lower() == 'yes'
    except (EOFError, KeyboardInterrupt, OSError):
        approved = False
    if not approved:
        return 'Command not executed: approval was not given.'
    return run_pipeline([['/bin/bash', '--noprofile', '--norc', '-c', command]])


def run_command(command):
    print(execute_command(command))
