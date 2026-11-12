"""Clear generated CEH-Exam logs only; preserve findings, keys and unrelated files."""
import argparse
from pathlib import Path
from exam_workflow import desktop,state_root,redirected

LOGS={'terminal.txt','commands.txt','commands.log','network-info.txt','network-info.json','init-review.txt','tool-index.json'}
STATE={'network-info.json','network-info.txt','evidence-index.jsonl','tool-index.json','last-task.json'}


def reset_logs(root,state,clear=False):
    root=Path(root);state=Path(state)
    if root.name!='CEH-Exam' or redirected(root) or redirected(state):raise RuntimeError('Unexpected or redirected reset root')
    targets=[]
    for parent,names in ((root,LOGS),(state,STATE)):
        if not parent.exists():continue
        for folder in parent.iterdir():
            if redirected(folder):raise RuntimeError('Redirected report/state folder refused')
            if not folder.is_dir():continue
            if folder.parent.resolve()!=parent.resolve():raise RuntimeError('Reset path escaped expected root')
            for name in names:
                path=folder/name
                if redirected(path):raise RuntimeError('Redirected log refused')
                if path.exists():
                    if not path.is_file():raise RuntimeError('Unexpected directory in place of a log')
                    targets.append(path)
    for path in targets:
        print(('Removing: ' if clear else 'Would remove: ')+str(path))
        if clear:path.unlink()
    # Empty old hostname folders can be removed; real findings are always kept.
    if clear and root.exists():
        for folder in root.iterdir():
            if not folder.is_dir() or redirected(folder):continue
            finding=folder/'findings.txt'
            if finding.is_file() and not redirected(finding) and finding.stat().st_size==0:finding.unlink()
            if not any(folder.iterdir()):folder.rmdir()
    return len(targets)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clear',action='store_true',help='Apply the reset; default is preview only')
    args=parser.parse_args()
    count=reset_logs(desktop()/'CEH-Exam',state_root(),args.clear)
    print(f'{count} generated log/state files '+('removed.' if args.clear else 'would be removed.'))

if __name__=='__main__':main()
