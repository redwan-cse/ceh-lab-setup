"""Remove only this per-user exam profile; keep Python and other SGPT installs."""
import argparse
import os
from pathlib import Path
import shutil
import sys
from setup_exam import ROOT,CONFIG,BASE


def redirected(path):
    return path.is_symlink() or getattr(path,'is_junction',lambda:False)()


def remove_tree(path,parent,dry_run=False):
    path=Path(path);parent=Path(parent)
    if path.resolve()==parent.resolve() or path.parent.resolve()!=parent.resolve() or redirected(path):
        raise RuntimeError('Refusing removal outside the expected dedicated directory')
    if path.exists():
        print(('Would remove: ' if dry_run else 'Removing: ')+str(path))
        if not dry_run:shutil.rmtree(path)


def clean_wrapper(path,runtime,dry_run=False):
    if not path.exists() and not path.is_symlink():return
    if redirected(path) or runtime not in path.read_text(encoding='utf-8'):
        raise RuntimeError('CLI wrapper was changed; refusing to overwrite it: '+str(path))
    backup=path.with_name(path.name+'.before-exam')
    if redirected(backup):raise RuntimeError('Redirected wrapper backup refused')
    if not dry_run:
        if backup.exists():os.replace(backup,path)
        else:path.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--keep-config',action='store_true',help='Keep exam key/history intentionally')
    args=parser.parse_args()
    if Path(sys.prefix).resolve()==(ROOT/'venv').resolve():raise RuntimeError('Run removal with system python/python3, not the exam venv Python')
    runtime=str(ROOT/'exam_runtime.py')
    if ROOT.exists():
        if redirected(ROOT) or not (ROOT/'exam_runtime.py').is_file():raise RuntimeError('Unknown installation directory; inspect manually')
        if 'ShellGPT exam entry point' not in (ROOT/'exam_runtime.py').read_text():raise RuntimeError('Unknown runtime; removal refused')
    if CONFIG.exists() and not args.keep_config:
        from setup_exam import read
        if read().get('API_BASE_URL')!=BASE:raise RuntimeError('Config provider changed; use --keep-config and inspect manually')
    bin_dir=ROOT/'bin' if os.name=='nt' else Path.home()/'.local'/'bin'
    names=['sgpt-exam.cmd','sgpt.cmd'] if os.name=='nt' else ['sgpt-exam','sgpt']
    # Validate all wrappers before modifying either one.
    for name in names:
        path=bin_dir/name
        if (path.exists() or path.is_symlink()) and (redirected(path) or runtime not in path.read_text(encoding='utf-8')):
            raise RuntimeError('Changed/unrelated wrapper; inspect before removal: '+str(path))
    for name in names:clean_wrapper(bin_dir/name,runtime,args.dry_run)
    if os.name=='nt' and not args.dry_run:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as reg:
            try:value,kind=winreg.QueryValueEx(reg,'Path')
            except FileNotFoundError:value,kind='',winreg.REG_EXPAND_SZ
            value=';'.join(p for p in value.split(';') if p.lower()!=str(bin_dir).lower())
            winreg.SetValueEx(reg,'Path',0,kind,value)
    elif os.name!='nt' and not args.dry_run:
        line='\n# ShellGPT exam commands\nexport PATH="$HOME/.local/bin:$PATH"\n'
        for name in ('.profile','.bashrc','.zshenv'):
            path=Path.home()/name
            if redirected(path):raise RuntimeError('Redirected shell profile refused')
            if path.exists():path.write_text(path.read_text().replace(line,''))
    remove_tree(ROOT,ROOT.parent,args.dry_run)
    if not args.keep_config:remove_tree(CONFIG,CONFIG.parent,args.dry_run)
    print('Dry run complete.' if args.dry_run else 'Exam profile removed. Open a new terminal. Shared Python and StepFun config were kept.')

if __name__=='__main__':main()
