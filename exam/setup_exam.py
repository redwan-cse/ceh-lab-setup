"""Isolated ShellGPT 1.5.1 + direct Google AI Studio Gemini exam installation."""
import argparse
import getpass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import venv


def windows_acl(path, directory=False):
    import json
    code=r'''$ErrorActionPreference='Stop'; $r=[Console]::In.ReadToEnd()|ConvertFrom-Json
$user=[Security.Principal.WindowsIdentity]::GetCurrent().User
if($r.directory){$acl=New-Object Security.AccessControl.DirectorySecurity}else{$acl=New-Object Security.AccessControl.FileSecurity}
$acl.SetAccessRuleProtection($true,$false)
foreach($sid in @($user,(New-Object Security.Principal.SecurityIdentifier('S-1-5-18')))){
 if($r.directory){$rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')}
 else{$rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')}
 $acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $r.path -AclObject $acl'''
    import base64
    powershell=Path(os.environ['SystemRoot'])/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    subprocess.run([str(powershell),'-NoProfile','-EncodedCommand',base64.b64encode(code.encode('utf-16-le')).decode()],
                   input=json.dumps(dict(path=str(path),directory=directory)),text=True,check=True)

BASE='https://generativelanguage.googleapis.com/v1beta/openai/'
MODEL='gemini-4-carbon'
CONFIG=Path.home()/'.config'/'shell_gpt_exam'
ROOT=Path.home()/'.local'/'share'/'shellgpt-exam'
if os.name=='nt':ROOT=Path(os.environ['LOCALAPPDATA'])/'CEHLab'/'shellgpt-exam'


def secure_config():
    if CONFIG.is_symlink() or (CONFIG/'.sgptrc').is_symlink():raise RuntimeError('Redirected exam config refused')
    CONFIG.mkdir(parents=True,exist_ok=True,mode=0o700)
    if os.name=='nt':
        windows_acl(CONFIG,directory=True)
    else:os.chmod(CONFIG,0o700)


def save(values):
    secure_config()
    (CONFIG/'.sgptrc').write_text(''.join(f'{k}={v}\n' for k,v in values.items()),encoding='utf-8')
    os.chmod(CONFIG/'.sgptrc',0o600)
    if os.name=='nt':windows_acl(CONFIG/'.sgptrc')


def read():
    path=CONFIG/'.sgptrc'
    if not path.exists():return {}
    if path.is_symlink() or CONFIG.is_symlink():raise RuntimeError('Redirected exam config refused')
    return dict(line.split('=',1) for line in path.read_text(encoding='utf-8').splitlines() if '=' in line and not line.startswith('#'))


def key_prompt(values):
    if values.get('API_BASE_URL')!=BASE:raise RuntimeError('Refusing a key for an unexpected provider')
    key=getpass.getpass('Google AI Studio API key (hidden; Enter keeps saved key): ')
    if '\r' in key or '\n' in key:raise ValueError('Key must be one line')
    if key:values['OPENAI_API_KEY']=key
    save(values)


def patch(path,before,after):
    text=path.read_text(encoding='utf-8')
    if text.count(before)!=1:raise RuntimeError('Unexpected ShellGPT source: '+path.name)
    text=text.replace(before,after)
    compile(text,str(path),'exec')
    path.write_text(text,encoding='utf-8')


def update_unix_paths():
    line='\n# ShellGPT exam commands\nexport PATH="$HOME/.local/bin:$PATH"\n'
    for name in ('.profile','.bashrc','.zshenv'):
        path=Path.home()/name
        if path.is_symlink():raise RuntimeError('Redirected shell profile refused')
        old=path.read_text() if path.exists() else ''
        # Prepend before Bash's noninteractive early-return block as well.
        path.write_text(line+old.replace(line,''))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-only',action='store_true')
    parser.add_argument('--no-key-prompt',action='store_true')
    parser.add_argument('--activate',action='store_true',help='Also make sgpt select this exam profile')
    parser.add_argument('--key-stdin',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--configure',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    assert sys.version_info>=(3,10),'Python 3.10+ required'
    if args.key_only:
        values=read()
        if args.key_stdin:
            if values.get('API_BASE_URL')!=BASE:raise RuntimeError('Unexpected key destination')
            key=sys.stdin.read().strip()
            if not key or '\n' in key or '\r' in key:raise ValueError('Expected one API key')
            values['OPENAI_API_KEY']=key;save(values)
        else:key_prompt(values)
        return
    resources=Path(__file__).resolve().parent
    if not args.configure:
        if ROOT.is_symlink() or (ROOT/'venv').is_symlink():raise RuntimeError('Redirected installation refused')
        python=ROOT/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        if not python.exists():venv.create(ROOT/'venv',with_pip=True)
        subprocess.run([str(python),'-m','pip','install','--upgrade','--force-reinstall','shell-gpt==1.5.1','typer==0.16.0','click==8.1.8','openai==2.54.0'],check=True)
        command=[str(python),str(Path(__file__).resolve()),'--configure']
        if args.no_key_prompt:command+=['--no-key-prompt']
        if args.activate:command+=['--activate']
        subprocess.run(command,check=True);return
    if sys.prefix==sys.base_prefix:raise RuntimeError('Dedicated venv required')
    secure_config()
    existing=read()
    key=existing.get('OPENAI_API_KEY','') if existing.get('API_BASE_URL')==BASE else ''
    settings=dict(OPENAI_API_KEY=key,API_BASE_URL=BASE,DEFAULT_MODEL=MODEL,REASONING_EFFORT='high',
        USE_LITELLM='false',OPENAI_USE_FUNCTIONS='true',OPENAI_FUNCTIONS_PATH=str(CONFIG/'functions'),
        ROLE_STORAGE_PATH=str(CONFIG/'roles'),CACHE_PATH=str(CONFIG/'cache'),CHAT_CACHE_PATH=str(CONFIG/'chats'),
        REQUEST_TIMEOUT='300',SHELL_NAME='powershell' if os.name=='nt' else 'bash',SHELL_INTERACTION='true',SHOW_FUNCTIONS_OUTPUT='true')
    save(settings)
    package=Path(sysconfig.get_path('purelib'))/'sgpt'
    patch(package/'config.py','Path(CONFIG_FOLDER) / "shell_gpt"','Path(CONFIG_FOLDER) / "shell_gpt_exam"')
    platform='windows' if os.name=='nt' else 'linux'
    guards=['shellgpt_command_guard.py','shellgpt_command_policy.ps1'] if os.name=='nt' else ['linux_command_guard.py']
    guard_source=resources.parent/'universal'/platform
    for name in guards:shutil.copyfile(guard_source/name,package/name)
    module='shellgpt_command_guard' if os.name=='nt' else 'linux_command_guard'
    function='''from pydantic import BaseModel, Field
from sgpt.GUARD import execute_command
class Function(BaseModel):
    """Execute a command. Inspection runs automatically; other commands need approval. Respect refusals."""
    shell_command: str = Field(..., description="Command to execute")
    @classmethod
    def execute(cls, shell_command): return execute_command(shell_command)
    @classmethod
    def openai_schema(cls):
        schema=cls.model_json_schema()
        return {"type":"function","function":{"name":"execute_shell_command","description":cls.__doc__,"parameters":{"type":"object","properties":schema["properties"],"required":schema["required"]}}}
'''.replace('GUARD',module)
    (CONFIG/'functions').mkdir(exist_ok=True)
    (CONFIG/'functions'/'execute_shell.py').write_text(function,encoding='utf-8')
    (package/'llm_functions'/'common'/'execute_shell.py').write_text(function,encoding='utf-8')
    utils=package/'utils.py';text=utils.read_text(encoding='utf-8')
    start=text.index('def run_command(command: str) -> None:');end=text.index('\n\ndef option_callback',start)
    replacement=f'def run_command(command: str) -> None:\n    from sgpt.{module} import run_command as guarded_run\n    guarded_run(command)\n'
    text=text[:start]+replacement+text[end:];compile(text,str(utils),'exec');utils.write_text(text,encoding='utf-8')
    app=package/'app.py';text=app.read_text(encoding='utf-8')
    start=text.index('    session: PromptSession[str] = PromptSession()');end=text.index('\n\ndef entry_point()',start)
    text=text[:start]+'    if shell and interaction:\n        run_command(full_completion)\n'+text[end:]
    compile(text,str(app),'exec');app.write_text(text,encoding='utf-8')
    runtime=ROOT/'exam_runtime.py';shutil.copyfile(resources/'exam_runtime.py',runtime)
    bin_dir=ROOT/'bin' if os.name=='nt' else Path.home()/'.local'/'bin'
    bin_dir.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        wrapper=f'@echo off\n"{sys.executable}" "{runtime}" %*\n'
        names=['sgpt-exam.cmd']+(['sgpt.cmd'] if args.activate else [])
    else:
        import shlex
        wrapper=f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(runtime))} "$@"\n'
        names=['sgpt-exam']+(['sgpt'] if args.activate else [])
    for name in names:
        target=bin_dir/name
        if target.is_symlink():raise RuntimeError('Refusing a redirected CLI wrapper')
        if name in ('sgpt','sgpt.cmd') and target.exists() and str(runtime) not in target.read_text(encoding='utf-8') and not target.with_name(name+'.before-exam').exists():
            shutil.copyfile(target,target.with_name(name+'.before-exam'))
        target.write_text(wrapper,encoding='utf-8',newline='\n');os.chmod(target,0o700)
    if os.name=='nt':
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as reg:
            try:old=winreg.QueryValueEx(reg,'Path')[0]
            except FileNotFoundError:old=''
            parts=[p for p in old.split(';') if p and p.lower()!=str(bin_dir).lower()]
            winreg.SetValueEx(reg,'Path',0,winreg.REG_EXPAND_SZ,str(bin_dir)+';'+ ';'.join(parts))
    else:
        update_unix_paths()
    if not args.no_key_prompt:key_prompt(settings)
    print('Exam setup ready. Open a new terminal; command: sgpt-exam')
    print('API key file: '+str(CONFIG/'.sgptrc'))

if __name__=='__main__':main()
