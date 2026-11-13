"""Versioned, reviewed lab scripts. Approved scripts use the current user's permissions.

This is an execution approval boundary, not an operating-system sandbox. Creating
or editing writes a new version only; each version receives AI or human approval
in the current chat process. No approval is persisted across processes.
No interpreters are installed. Windows PowerShell uses a child-process execution
policy flag; no persistent execution-policy or Group Policy changes are made.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
from terminal_ui import ApprovalRefusal,interactive_input
from file_locking import file_lock


_TIMEOUT_SECONDS = 120
_LANGUAGES = {
    'python': ('python', '.py'), 'py': ('python', '.py'), '.py': ('python', '.py'),
    'bash': ('bash', '.sh'), 'shell': ('bash', '.sh'), 'sh': ('bash', '.sh'), '.sh': ('bash', '.sh'),
    'powershell': ('powershell', '.ps1'), 'ps1': ('powershell', '.ps1'), '.ps1': ('powershell', '.ps1'),
    'batch': ('batch', '.bat'), 'bat': ('batch', '.bat'), '.bat': ('batch', '.bat'),
    'cmd': ('batch', '.cmd'), '.cmd': ('batch', '.cmd'),
}
_VERSION_NAME = re.compile(r'scripts_[A-Za-z0-9][A-Za-z0-9_-]*_[1-9][0-9]*\.(?:py|sh|ps1|bat|cmd)\Z')


def _windows():
    return os.name == 'nt'


def _safe_path(path):
    """Reject redirects in every ancestor, including Windows junctions/reparse points."""
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Redirected script or state path refused')
    return path


class LabScripts:
    def __init__(self, workflow, input_reader=None,approval_reviewer=None):
        self.workflow = workflow
        self.folder = Path(workflow.folder).absolute() / 'scripts'
        self.index = Path(workflow.state).absolute() / 'scripts-index.json'
        self._approved_versions=set()
        self.input_reader=input_reader or interactive_input
        self.approval_reviewer=approval_reviewer

    def _records(self):
        _safe_path(self.folder)
        _safe_path(self.index)
        if not self.index.exists():
            return {}
        records = json.loads(self.index.read_text(encoding='utf-8'))
        if not isinstance(records, dict):
            raise ValueError('Invalid script ownership index')
        return records

    def write(self, name, language, content):
        """Create the next exclusive version, record its digest, and display its source."""
        _safe_path(self.index)
        with file_lock(self.index.with_suffix('.lock')):
            metadata=self._write(name,language,content)
        self.workflow.emit('Saved new script version: '+metadata['path']+'\nSHA256: '+metadata['sha256']+'\nSOURCE:\n'+content)
        return metadata

    def _write(self,name,language,content):
        if not isinstance(language, str) or language.lower() not in _LANGUAGES:
            raise ValueError('Use Python, Bash/shell, PowerShell, or Windows batch/cmd')
        language, extension = _LANGUAGES[language.lower()]
        records = self._records()
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', name):
            raise ValueError('Use a simple script name without paths, spaces, or shell characters')
        stem = name
        if Path(stem).suffix.lower() in {'.py', '.sh', '.ps1', '.bat', '.cmd'}:
            stem = stem.rsplit('.', 1)[0]
        if stem.startswith('scripts_'):
            stem = re.sub(r'_[1-9][0-9]*$', '', stem[len('scripts_'):])
        else:
            edited=re.fullmatch(r'(.+)_([1-9][0-9]*)',stem)
            if edited and any(re.fullmatch(r'scripts_'+re.escape(edited.group(1))+r'_[1-9][0-9]*\.(?:py|sh|ps1|bat|cmd)',old) for old in records):
                stem=edited.group(1)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', stem) or re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])', stem, re.I):
            raise ValueError('Unsafe script filename')
        if not isinstance(content, str) or not content.strip() or '\0' in content:
            raise ValueError('Supply nonempty script source without null bytes')
        if self.workflow.redact(content) != content:
            raise ValueError('Known API credentials/secrets cannot be stored in scripts')
        self.folder.mkdir(mode=0o700, exist_ok=True)
        _safe_path(self.folder)
        prefix = 'scripts_' + stem + '_'
        pattern = re.compile(re.escape(prefix) + r'([1-9][0-9]*)\.(?:py|sh|ps1|bat|cmd)\Z')
        versions = [int(match.group(1)) for entry in self.folder.iterdir() if (match := pattern.fullmatch(entry.name))]
        number = max(versions, default=0) + 1
        data = content.encode('utf-8')
        while True:
            path = self.folder / (prefix + str(number) + extension)
            _safe_path(path)
            try:
                # Exclusive creation never replaces existing files or earlier versions.
                with path.open('xb') as stream:
                    os.chmod(path, 0o600)
                    stream.write(data)
                break
            except FileExistsError:
                number += 1
        metadata = dict(script=path.name, path=str(path), language=language, sha256=hashlib.sha256(data).hexdigest())
        records[path.name] = metadata
        _safe_path(self.index)
        self.workflow.write(self.index.name, json.dumps(records, ensure_ascii=False, indent=2))
        return metadata

    def _owned(self, script):
        if not isinstance(script, str) or not script or '\0' in script:
            raise ValueError('Supply a previously created script filename or its absolute path')
        requested = Path(script)
        if requested.is_absolute():
            if requested.parent != self.folder:
                raise ValueError('Only this lab script folder may be used')
            name = requested.name
        else:
            name = script
        if not _VERSION_NAME.fullmatch(name):
            raise ValueError('Unsafe or unversioned script filename')
        records = self._records()
        record = records.get(name)
        if not isinstance(record, dict) or record.get('script') != name:
            raise ValueError('Script is not a previously created owned version')
        path = _safe_path(self.folder / name)
        if not path.is_file():
            raise ValueError('Script version is unavailable')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record.get('sha256'):
            raise ValueError('Script content changed; create a new version before review and execution')
        return path, record

    def _git_bash(self):
        candidates = []
        for variable, suffix in [('ProgramFiles', 'Git/bin/bash.exe'), ('ProgramFiles(x86)', 'Git/bin/bash.exe'), ('LOCALAPPDATA', 'Programs/Git/bin/bash.exe')]:
            if os.environ.get(variable):
                candidates.append(Path(os.environ[variable]) / suffix)
        git = shutil.which('git.exe')
        if git:
            candidates.append(Path(git).parent.parent / 'bin/bash.exe')
        for candidate in candidates:
            if candidate.is_file():
                # Git for Windows ships bash alongside its msys runtime.
                root = candidate.parent.parent
                if (root / 'usr/bin/msys-2.0.dll').is_file():
                    return str(candidate)
        raise ValueError('Git Bash is not installed. Use Python or PowerShell, or another compatible installed language; no runtime was installed.')

    def _command(self, path, language):
        if language == 'python' and path.suffix == '.py':
            return [sys.executable, path.name]
        if language == 'bash' and path.suffix == '.sh':
            binary = self._git_bash() if _windows() else shutil.which('bash')
            if binary:
                return [binary, path.name]
        elif language == 'powershell' and path.suffix == '.ps1':
            if _windows():
                binary = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
                binary = str(binary) if binary.is_file() else None
            else:
                binary = shutil.which('pwsh')
            if binary:
                policy = ['-ExecutionPolicy', 'Bypass'] if _windows() else []
                return [binary, '-NoProfile', '-NonInteractive', *policy, '-File', path.name]
        elif language == 'batch' and path.suffix in ('.bat', '.cmd'):
            if not _windows():
                raise ValueError('Batch/cmd scripts require Windows. Use a compatible installed language; no runtime was installed.')
            binary = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/cmd.exe'
            if binary.is_file():
                # Basename is strictly validated, so cmd receives no metacharacters or path spaces.
                return [str(binary), '/d', '/c', path.name]
        raise ValueError('Required script runtime is not installed or language/extension is invalid. Use a compatible installed language; no runtime was installed.')

    def _stop(self, process):
        if _windows():
            killer = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/taskkill.exe'
            try:
                subprocess.run([str(killer), '/PID', str(process.pid), '/T', '/F'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()

    def run(self, script):
        """Run an unchanged owned version after approval review in this process."""
        path, record = self._owned(script)
        argv = self._command(path, record.get('language'))
        command = subprocess.list2cmdline(argv)

        def runner(_command):
            approval=(path.name,record['sha256'])
            ai_approved=False
            if approval not in self._approved_versions and self.approval_reviewer:
                try:ai_approved=self.approval_reviewer(command,path)
                except Exception:ai_approved=False
            if approval not in self._approved_versions and not ai_approved:
                try:
                    answer = self.input_reader('Approve this version ' + path.name + ' (SHA256 ' + record['sha256'] + ') for this chat with your full current user permissions? Review its source and installation/deletion actions. Type yes to run: ')
                except (EOFError,OSError,KeyboardInterrupt):
                    return ApprovalRefusal('Execution declined (no interactive approval).')
                if answer.strip().lower() != 'yes':
                    return ApprovalRefusal('Execution declined; no script was launched.')
            # Revalidate after the human review pause, before interpreter startup.
            self._owned(path.name)
            self._approved_versions.add(approval)
            options = dict(cwd=str(self.folder), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            if _windows():
                options['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                options['start_new_session'] = True
            process = subprocess.Popen(argv, **options)
            timed_out = False
            try:
                output, error = process.communicate(timeout=_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                timed_out = True
                self._stop(process)
                try:
                    output, error = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.stdout.close()
                    process.stderr.close()
                    output, error = '', 'Child output streams did not close after termination.'
            except BaseException:
                self._stop(process)
                raise
            status = 'Timed out after ' + str(_TIMEOUT_SECONDS) + ' seconds; process group terminated.\n' if timed_out else ''
            return status + 'Exit code: ' + str(process.returncode) + '\nSTDOUT:\n' + output + '\nSTDERR:\n' + error

        return self.workflow.execute(command, runner)
