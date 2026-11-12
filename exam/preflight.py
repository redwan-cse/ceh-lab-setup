"""Small prerequisite check. Installs only after one explicit local consent."""
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import re

PACKAGES={'shell-gpt':'1.5.1','openai':'2.54.0','typer':'0.16.0','click':'8.1.8'}


def missing_packages():
    missing=[]
    for name,version in PACKAGES.items():
        try:ready=importlib.metadata.version(name)==version
        except importlib.metadata.PackageNotFoundError:ready=False
        if not ready:missing.append(name+'=='+version)
    return missing


def consent(plan):
    print('Missing prerequisites: '+', '.join(plan))
    print('Only the private ShellGPT environment and listed prerequisites will be changed. No system upgrade or network/security configuration changes.')
    if not sys.stdin.isatty():
        print('No interactive approval available. Nothing installed. Run sgpt in a terminal to approve repair.');return False
    return input('Install these prerequisites now? [y/N] ').strip().lower() in ('y','yes')


def ensure(for_init=False,approve=consent):
    packages=missing_packages()
    needs_ip=for_init and os.name!='nt' and not shutil.which('ip')
    plan=packages+(['iproute2 (system package)'] if needs_ip else [])
    if not plan:return True
    if not approve(plan):return False
    # Never run pip in a shared/system Python environment.
    root=Path(__file__).resolve().parent
    if Path(sys.prefix).resolve()!=(root/'venv').resolve():
        print('Repair refused outside the private ShellGPT environment. Rerun the OS setup script.');return False
    if needs_ip:
        release=Path('/etc/os-release').read_text(encoding='utf-8')
        if not any(line in release.splitlines() for line in ('ID=parrot','ID=debian','ID=ubuntu')) or not shutil.which('apt-get'):
            print('Automatic OS package repair is unsupported here; no changes made.');return False
        sudo=[] if os.geteuid()==0 else ['sudo']
        environment=dict(os.environ,LC_ALL='C')
        preview=subprocess.run(['apt-get','--simulate','install','--no-upgrade','--no-remove','--no-install-recommends','iproute2'],capture_output=True,text=True,env=environment)
        if preview.returncode or re.search(r'(?m)^(?:Remv |Inst \S+ \[)',preview.stdout):
            print('OS prerequisite repair needs an upgrade/removal or cannot be resolved. Nothing installed; stop and review manually.');return False
        result=subprocess.run([*sudo,'apt-get','install','--no-upgrade','--no-remove','--no-install-recommends','-y','iproute2'])
        if result.returncode:return False
    if packages:
        if importlib.util.find_spec('pip') is None:
            if subprocess.run([sys.executable,'-m','ensurepip']).returncode:return False
        result=subprocess.run([sys.executable,'-m','pip','install',*packages])
        if result.returncode:return False
        # Reapply this kit's guards after a repaired shell-gpt package.
        result=subprocess.run([sys.executable,str(root/'setup_exam.py'),'--configure','--activate','--no-key-prompt'])
        if result.returncode:return False
    ready=not missing_packages() and (not needs_ip or bool(shutil.which('ip')))
    if not ready:print('Prerequisite verification failed. No task commands were run.')
    return ready


if __name__=='__main__':
    try:sys.exit(0 if ensure('--for-init' in sys.argv) else 3)
    except (OSError,ValueError,EOFError):
        print('Prerequisite check/repair failed. No task commands were run. Rerun the OS setup script.',file=sys.stderr);sys.exit(3)
