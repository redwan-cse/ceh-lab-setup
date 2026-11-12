"""Isolated ShellGPT 1.5.1 exam installation with explicit provider profiles."""
import argparse
import getpass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import venv
import json
import tempfile
import uuid
import re
from providers import PROFILES, GOOGLE_BASE, STEP_BASE, select_profile


def windows_acl(path, directory=False):
    import json
    code=r'''$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $env:PSModulePath=Join-Path $PSHOME 'Modules'; $r=[Console]::In.ReadToEnd()|ConvertFrom-Json
$user=[Security.Principal.WindowsIdentity]::GetCurrent().User
if($r.directory){$acl=New-Object Security.AccessControl.DirectorySecurity}else{$acl=New-Object Security.AccessControl.FileSecurity}
$acl.SetAccessRuleProtection($true,$false)
foreach($sid in @($user,(New-Object Security.Principal.SecurityIdentifier('S-1-5-18')))){
 if($r.directory){$rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')}
 else{$rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')}
 $acl.AddAccessRule($rule)
}
if($r.directory){[IO.Directory]::SetAccessControl($r.path,$acl)}else{[IO.File]::SetAccessControl($r.path,$acl)}'''
    import base64
    powershell=Path(os.environ['SystemRoot'])/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    subprocess.run([str(powershell),'-NoProfile','-EncodedCommand',base64.b64encode(code.encode('utf-16-le')).decode()],
                   input=json.dumps(dict(path=str(path),directory=directory)),text=True,check=True,capture_output=True)

BASE=GOOGLE_BASE
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


def atomic_private_write(path,text):
    if path.is_symlink():raise RuntimeError('Redirected private file refused')
    descriptor,temporary=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    temporary=Path(temporary)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8',newline='\n') as handle:
            handle.write(text);handle.flush();os.fsync(handle.fileno())
        os.chmod(temporary,0o600)
        if os.name=='nt':windows_acl(temporary)
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()


def save(values):
    secure_config()
    atomic_private_write(CONFIG/'.sgptrc',''.join(f'{k}={v}\n' for k,v in values.items()))


def read():
    path=CONFIG/'.sgptrc'
    if not path.exists():return {}
    if path.is_symlink() or CONFIG.is_symlink():raise RuntimeError('Redirected exam config refused')
    return dict(line.split('=',1) for line in path.read_text(encoding='utf-8').splitlines() if '=' in line and not line.startswith('#'))


def load_keys(directory=None):
    path=(Path(directory) if directory else CONFIG)/'provider-keys.json'
    if not path.exists():return {}
    if path.is_symlink() or path.parent.is_symlink():raise RuntimeError('Redirected key store refused')
    values=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(values,dict) or any(k not in {p['key'] for p in PROFILES.values()} or not isinstance(v,str) for k,v in values.items()):raise RuntimeError('Invalid provider key store')
    return values


def remember_key(values):
    key=values.get('OPENAI_API_KEY','')
    if not key:return
    matches=[p['key'] for p in PROFILES.values() if p['base'].rstrip('/')==values.get('API_BASE_URL','').rstrip('/')]
    if not matches:raise RuntimeError('Unexpected key provider')
    secure_config();keys=load_keys();keys[matches[0]]=key
    path=CONFIG/'provider-keys.json'
    if path.is_symlink():raise RuntimeError('Redirected key store refused')
    atomic_private_write(path,json.dumps(keys))


def require_owned_install():
    runtime=ROOT/'exam_runtime.py'
    if ROOT.is_symlink() or (ROOT/'venv').is_symlink() or runtime.is_symlink():
        raise RuntimeError('Redirected installation refused')
    if not runtime.is_file() or not runtime.read_text(encoding='utf-8').startswith('"""ShellGPT exam entry point'):
        raise RuntimeError('Install the owned exam runtime before changing this installation')


def switch_provider(name,prompt=True):
    require_owned_install()
    active=read()
    selected=select_profile(active,name,load_keys())
    if not selected.get('OPENAI_API_KEY'):
        if not prompt:raise RuntimeError('No saved key for '+name+'; active provider kept')
        key=getpass.getpass(name+' API key (hidden; Enter cancels): ')
        if not key:raise RuntimeError('No key supplied; active provider kept')
        if '\n' in key or '\r' in key:raise ValueError('Key must be one line')
        selected['OPENAI_API_KEY']=key
    remember_key(active)
    remember_key(selected)
    save(selected)
    print('Provider: '+selected['EXAM_PROFILE'])
    print('Model: '+selected['DEFAULT_MODEL'])
    print('Endpoint: '+selected['API_BASE_URL'])


def key_prompt(values,save_active=True):
    if values.get('API_BASE_URL') not in {p['base'] for p in PROFILES.values()}:raise RuntimeError('Refusing a key for an unexpected provider')
    key=getpass.getpass(values.get('EXAM_PROFILE','Provider')+' API key (hidden; Enter keeps saved key): ')
    if '\r' in key or '\n' in key:raise ValueError('Key must be one line')
    if key:values['OPENAI_API_KEY']=key
    if save_active:save(values)
    remember_key(values)


def patch(path,before,after):
    text=path.read_text(encoding='utf-8')
    if before not in text and text.count(after)==1:return
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


def notify_windows_environment():
    """Tell Explorer/new desktop processes to reload the saved user environment."""
    import ctypes
    try:
        send=ctypes.windll.user32.SendMessageTimeoutW
        send.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_wchar_p,
                       ctypes.c_uint,ctypes.c_uint,ctypes.POINTER(ctypes.c_size_t)]
        send.restype=ctypes.c_ssize_t
        result=ctypes.c_size_t()
        return bool(send(0xffff,0x001a,0,'Environment',0x0002,2000,ctypes.byref(result)))
    except (AttributeError,OSError):return False


def update_windows_paths(bin_dir):
    import winreg
    key=lambda value:os.path.expandvars(value.strip().strip('"')).replace('/','\\').rstrip('\\').casefold()
    def prepend(value):return str(bin_dir)+';'+';'.join(part for part in value.split(';') if part and key(part)!=key(str(bin_dir)))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as reg:
        try:old=winreg.QueryValueEx(reg,'Path')[0]
        except FileNotFoundError:old=''
        winreg.SetValueEx(reg,'Path',0,winreg.REG_EXPAND_SZ,prepend(old))
    os.environ['PATH']=prepend(os.environ.get('PATH',''))
    if not notify_windows_environment():
        print('User PATH saved; desktop notification was unavailable. Prepend the command folder to the current terminal PATH or use the full sgpt.cmd path.')


def copy_references(resources):
    source=resources.parent/'docs'/'ceh-tools'
    if not source.is_dir():source=resources/'references'
    target=ROOT/'references'
    if source.is_symlink() or target.is_symlink():raise RuntimeError('Redirected reference directory refused')
    if not source.is_dir():raise RuntimeError('Keep docs/ceh-tools with the setup kit')
    target.mkdir(exist_ok=True)
    for path in source.glob('*.md'):
        destination=target/path.name
        if path.is_symlink() or destination.is_symlink():raise RuntimeError('Redirected reference refused')
        if path.resolve()!=destination.resolve():shutil.copyfile(path,destination)


def redirected_cli(path):
    return path.is_symlink() or getattr(path,'is_junction',lambda:False)()


def owned_wrapper(path,runtime):
    if redirected_cli(path) or not path.is_file():return False
    try:return str(runtime) in path.read_text(encoding='utf-8')
    except (UnicodeError,OSError):return False


def validate_cli_backup(backup,target,kind=None):
    # Resolve the parent only: a pipx backup is itself a link to another install.
    if (not backup.is_absolute() or backup.parent!=target.absolute().parent
            or backup.parent.resolve()!=target.parent.resolve()
            or not re.fullmatch(re.escape(target.name)+r'\.before-exam(?:-[A-Za-z0-9_-]+)?',backup.name)):
        raise RuntimeError('CLI backup outside the expected command directory refused')
    actual='symlink' if backup.is_symlink() else 'file'
    if getattr(backup,'is_junction',lambda:False)() or (actual=='file' and not backup.is_file()):
        raise RuntimeError('Missing or invalid CLI backup: '+str(backup))
    if kind is not None and kind!=actual:raise RuntimeError('CLI backup kind changed; inspect manually')
    return backup


def load_cli_backup(bin_dir,target):
    manifest=ROOT/'cli-backup.json'
    if redirected_cli(ROOT) or redirected_cli(bin_dir) or redirected_cli(manifest):
        raise RuntimeError('Redirected CLI backup metadata refused')
    if not manifest.exists():return None
    try:
        record=json.loads(manifest.read_text(encoding='utf-8'))
        if (record.get('version')!=1 or record.get('ownedPath')!=str(target.absolute())
                or record.get('kind') not in ('file','symlink')):
            raise ValueError('Unexpected CLI backup record')
        backup=Path(record['backupPath'])
    except (ValueError,TypeError,KeyError,AttributeError) as error:
        raise RuntimeError('Invalid CLI backup metadata; inspect manually') from error
    return validate_cli_backup(backup,target,record['kind'])


def write_wrappers(profile=None,activate=False,local_lab=False):
    runtime=ROOT/'exam_runtime.py'
    bin_dir=ROOT/'bin' if os.name=='nt' else Path.home()/'.local'/'bin'
    if redirected_cli(ROOT) or redirected_cli(bin_dir):raise RuntimeError('Redirected CLI directory refused')
    bin_dir.mkdir(parents=True,exist_ok=True)
    suffix='.cmd' if os.name=='nt' else ''
    target=bin_dir/('sgpt'+suffix)
    previous=load_cli_backup(bin_dir,target)
    moved=None
    if (target.exists() or target.is_symlink()) and not owned_wrapper(target,runtime):
        if previous is not None:raise RuntimeError('CLI wrapper changed while an original backup is pending; inspect manually')
        if getattr(target,'is_junction',lambda:False)() or (not target.is_symlink() and not target.is_file()):
            raise RuntimeError('Unsupported CLI wrapper; inspect manually: '+str(target))
        kind='symlink' if target.is_symlink() else 'file'
        # mkstemp reserves a unique name without replacing any older backup.
        descriptor,name=tempfile.mkstemp(prefix=target.name+'.before-exam-',dir=bin_dir)
        os.close(descriptor)
        moved=Path(name)
        try:os.replace(target,moved)
        except BaseException:
            moved.unlink()
            raise
    if os.name=='nt':
        wrapper=f'@echo off\nrem Owned exam runtime: {runtime}\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "{ROOT / "Launch-Sgpt.ps1"}" %*\n'
    else:
        import shlex
        wrapper=f'#!/bin/sh\n# Owned exam runtime: {runtime}\nexec {shlex.quote(str(ROOT / "launch-sgpt.sh"))} "$@"\n'
    try:
        if moved is not None:
            atomic_private_write(ROOT/'cli-backup.json',json.dumps(dict(version=1,
                ownedPath=str(target.absolute()),backupPath=str(moved.absolute()),kind=kind)))
        atomic_private_write(target,wrapper)
        os.chmod(target,0o700)
    except BaseException:
        if moved is not None:
            # A failed restore leaves the backup and metadata in place for recovery.
            try:os.replace(moved,target)
            except OSError as error:
                raise RuntimeError('Setup failed; original CLI preserved at '+str(moved)) from error
            manifest=ROOT/'cli-backup.json'
            if manifest.exists():manifest.unlink()
        raise
    for name in ('sgpt-exam','sgpt-lab'):
        alias=bin_dir/(name+suffix)
        if owned_wrapper(alias,runtime):alias.unlink()
    return bin_dir


RUNTIME_RESOURCES=('exam_runtime.py','exam_workflow.py','LAB-RULES.md','setup_exam.py','providers.py',
                   'Switch-Model.ps1','switch-model.sh','Launch-Sgpt.ps1','launch-sgpt.sh','preflight.py',
                   'collect-host-windows.ps1','collect-host-parrot.sh','Setup-Exam.ps1','setup-exam.sh','bootstrap-python-linux.sh','terminal_ui.py','lab_scripts.py','Activate-Sgpt.ps1')


def copy_runtime_resources(resources):
    for name in RUNTIME_RESOURCES:
        source=resources/name;target=ROOT/name
        if source.is_symlink() or target.is_symlink():raise RuntimeError('Redirected runtime resource refused: '+name)
        if source.is_file() and source.resolve()!=target.resolve():shutil.copyfile(source,target)
        if target.is_file() and target.suffix=='.sh':os.chmod(target,0o700)
    copy_references(resources)
    platform='windows' if os.name=='nt' else 'linux'
    guard_source=resources.parent/'universal'/platform
    if not guard_source.is_dir():guard_source=resources/'guard-sources'/platform
    guards=('shellgpt_command_guard.py','shellgpt_command_policy.ps1') if os.name=='nt' else ('linux_command_guard.py',)
    target=ROOT/'guard-sources'/platform
    if guard_source.is_symlink() or target.is_symlink():raise RuntimeError('Redirected guard sources refused')
    target.mkdir(parents=True,exist_ok=True)
    for name in guards:
        source=guard_source/name;destination=target/name
        if source.is_symlink() or destination.is_symlink():raise RuntimeError('Redirected guard source refused')
        if source.resolve()!=destination.resolve():shutil.copyfile(source,destination)


def prepare_venv():
    private=ROOT/'venv'
    python=private/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if ROOT.is_symlink() or private.is_symlink() or getattr(private,'is_junction',lambda:False)():raise RuntimeError('Redirected installation refused')
    healthy=False
    if python.exists():
        try:healthy=subprocess.run([str(python),'-c','import sys; assert sys.version_info >= (3,10); import ssl'],capture_output=True).returncode==0
        except OSError:pass
    if not healthy:
        if private.exists():
            require_owned_install()
            backup=ROOT/('venv.before-repair-'+uuid.uuid4().hex[:12])
            if private.resolve().parent!=ROOT.resolve() or backup.resolve().parent!=ROOT.resolve():raise RuntimeError('Repair path outside private installation refused')
            os.replace(private,backup)
            print('Preserved damaged private environment: '+str(backup))
        venv.create(private,with_pip=True)
    return python


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-only',action='store_true')
    parser.add_argument('--no-key-prompt',action='store_true')
    parser.add_argument('--activate',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--local-lab',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--key-stdin',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--configure',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--provider',choices=PROFILES)
    parser.add_argument('--switch-provider',action='store_true',help='Select the active provider without package changes or API calls')
    parser.add_argument('--profile-only',action='store_true',help='Switch an existing exam installation without reinstalling packages')
    parser.add_argument('--reuse-stepfun-key',action='store_true',help='Import the existing same-account StepFun key after checking its endpoint')
    args=parser.parse_args()
    assert sys.version_info>=(3,10),'Python 3.10+ required'
    if args.switch_provider:
        if not args.provider:parser.error('--switch-provider requires --provider')
        switch_provider(args.provider,prompt=not args.no_key_prompt)
        return
    if args.key_only:
        active=read()
        values=select_profile(active,args.provider,load_keys()) if args.provider else active
        save_active=not args.provider or args.provider==active.get('EXAM_PROFILE')
        if args.key_stdin:
            if values.get('API_BASE_URL') not in {p['base'] for p in PROFILES.values()}:raise RuntimeError('Unexpected key destination')
            key=sys.stdin.read().strip()
            if not key or '\n' in key or '\r' in key:raise ValueError('Expected one API key')
            values['OPENAI_API_KEY']=key
            if save_active:save(values)
            remember_key(values)
        else:key_prompt(values,save_active=save_active)
        return
    resources=Path(__file__).resolve().parent
    if args.profile_only:require_owned_install()
    if not args.configure and not args.profile_only:
        if ROOT.is_symlink() or (ROOT/'venv').is_symlink():raise RuntimeError('Redirected installation refused')
        python=prepare_venv()
        subprocess.run([str(python),'-m','pip','install','shell-gpt==1.5.1','typer==0.16.0','click==8.1.8','openai==2.54.0'],check=True)
        command=[str(python),str(Path(__file__).resolve()),'--configure']
        if args.no_key_prompt:command+=['--no-key-prompt']
        if args.activate:command+=['--activate']
        if args.provider:command+=['--provider',args.provider]
        if args.reuse_stepfun_key:command+=['--reuse-stepfun-key']
        subprocess.run(command,check=True);return
    if not args.profile_only and sys.prefix==sys.base_prefix:raise RuntimeError('Dedicated venv required')
    secure_config()
    existing=read()
    remember_key(existing)
    if args.reuse_stepfun_key:
        old=Path.home()/'.config/shell_gpt/.sgptrc'
        if old.exists() and not old.is_symlink():
            imported=dict(line.split('=',1) for line in old.read_text().splitlines() if '=' in line)
            if imported.get('API_BASE_URL','').rstrip('/')!=STEP_BASE.rstrip('/'):raise RuntimeError('Existing StepFun endpoint does not match; key not imported')
            remember_key(imported)
    selected=select_profile(existing,args.provider or existing.get('EXAM_PROFILE','openrouter-deepseek'),load_keys())
    settings=dict(selected,
        USE_LITELLM='false',OPENAI_USE_FUNCTIONS='true',OPENAI_FUNCTIONS_PATH=str(CONFIG/'functions'),
        ROLE_STORAGE_PATH=str(CONFIG/'roles'),CACHE_PATH=str(CONFIG/'cache'),CHAT_CACHE_PATH=str(CONFIG/'chats'),
        REQUEST_TIMEOUT='90',SHELL_NAME='powershell' if os.name=='nt' else 'bash',SHELL_INTERACTION='true',SHOW_FUNCTIONS_OUTPUT='true')
    save(settings)
    if args.profile_only:
        copy_runtime_resources(resources)
        bin_dir=write_wrappers(settings['EXAM_PROFILE'],args.activate,args.local_lab)
        if os.name=='nt':update_windows_paths(bin_dir)
        if not args.no_key_prompt:key_prompt(settings)
        print('Active provider: '+settings['EXAM_PROFILE']);return
    package=Path(sysconfig.get_path('purelib'))/'sgpt'
    patch(package/'config.py','Path(CONFIG_FOLDER) / "shell_gpt"','Path(CONFIG_FOLDER) / "shell_gpt_exam"')
    platform='windows' if os.name=='nt' else 'linux'
    guards=['shellgpt_command_guard.py','shellgpt_command_policy.ps1'] if os.name=='nt' else ['linux_command_guard.py']
    guard_source=resources.parent/'universal'/platform
    if not guard_source.is_dir():guard_source=resources/'guard-sources'/platform
    bundled=ROOT/'guard-sources'/platform
    bundled.mkdir(parents=True,exist_ok=True)
    for name in guards:
        source=guard_source/name
        if source.is_symlink() or (bundled/name).is_symlink():raise RuntimeError('Redirected guard source refused')
        if source.resolve()!=(bundled/name).resolve():shutil.copyfile(source,bundled/name)
        shutil.copyfile(source,package/name)
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
    original='    session: PromptSession[str] = PromptSession()'
    replacement='    if shell and interaction:\n        run_command(full_completion)\n'
    if original in text:
        start=text.index(original);end=text.index('\n\ndef entry_point()',start)
        text=text[:start]+replacement+text[end:]
    elif text.count(replacement)!=1:raise RuntimeError('Unexpected ShellGPT interaction source; repair stopped')
    compile(text,str(app),'exec');app.write_text(text,encoding='utf-8')
    copy_runtime_resources(resources)
    bin_dir=write_wrappers(settings['EXAM_PROFILE'],args.activate,args.local_lab)
    if os.name=='nt':
        update_windows_paths(bin_dir)
    else:
        update_unix_paths()
    if not args.no_key_prompt:key_prompt(settings)
    print('Exam setup ready. Open a new terminal; command: sgpt')
    print('API key file: '+str(CONFIG/'.sgptrc'))

if __name__=='__main__':main()
