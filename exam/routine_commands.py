"""Literal Linux task plans; automatic execution never invokes a shell.

Unknown code and system-changing commands fall back to the normal approval
guard. This is a workflow approval aid, not an operating-system sandbox.
"""
import os
from pathlib import Path
import re
import shlex
import stat
from urllib.parse import urlsplit


def _no_redirect(path):
    for item in (path,*path.parents):
        try:info=item.lstat()
        except FileNotFoundError:continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Redirected output path')


def _output(value,cwd,root,append=False):
    path=Path(value)
    if not path.is_absolute():path=cwd/path
    _no_redirect(path)
    path=path.resolve()
    parts=path.relative_to(root).parts
    if not parts or any(p.startswith('.') for p in parts) or path.name.casefold() in ('terminal.md','terminal.txt','findings.txt'):
        raise ValueError('Reserved evidence path')
    if not path.parent.is_dir() or (path.exists() and (not append or not path.is_file())):
        raise ValueError('Existing evidence or missing parent')
    return str(path)


def _sort_safe(args):
    for index,arg in enumerate(args):
        if not arg.startswith('-') or arg=='-':continue
        if arg in ('--','--help','--version','--unique','--reverse','--numeric-sort','--human-numeric-sort','--ignore-case','--general-numeric-sort','--version-sort','--stable','--check'):continue
        if arg.startswith(('--key=','--field-separator=')):continue
        if arg in ('-k','-t') and index+1<len(args):continue
        if re.fullmatch(r'-[bdfghinMnrRsuvVz]+',arg) or re.fullmatch(r'-[kt].+',arg):continue
        return False
    return True


def _uniq_safe(args):
    operands=[];index=0
    while index<len(args):
        arg=args[index];index+=1
        if arg in ('-f','-s','-w','--skip-fields','--skip-chars','--check-chars'):
            if index>=len(args) or not args[index].isdigit():return False
            index+=1
        elif arg.startswith('-'):
            if not (re.fullmatch(r'-[cduiz]+',arg) or re.fullmatch(r'-[fsw]\d+',arg) or arg in ('--count','--repeated','--unique','--ignore-case','--zero-terminated','--help','--version')):return False
        else:operands.append(arg)
    return len(operands)<=1  # A second positional operand is an output file.


def _curl(args,cwd,root):
    values={'-A','--user-agent','-H','--header','-e','--referer','--max-time','--connect-timeout','--max-redirs','-X','--request','--url','-o','--output'}
    flags={'--silent','--show-error','--location','--head','--get','--fail','--fail-with-body','--compressed','--verbose','--http1.1','--http2'}
    result=['--disable','--proto','=http,https','--proto-redir','=http,https','--connect-timeout','15','--max-time','120','--max-redirs','5']
    outputs=[];urls=[];index=0
    while index<len(args):
        arg=args[index];index+=1
        option,sep,attached=arg.partition('=') if arg.startswith('--') else (arg,'','')
        if arg.startswith('-o') and not arg.startswith('--') and len(arg)>2:option,sep,attached='-o','=',arg[2:]
        if option in values:
            if sep:value=attached
            else:
                if index>=len(args):raise ValueError('Missing curl option value')
                value=args[index];index+=1
            if option in ('-o','--output') and value!='-':
                value=_output(value,cwd,root);outputs.append(value)
                if len(outputs)>1:raise ValueError('Multiple curl outputs')
            elif option in ('-X','--request') and value.upper() not in ('GET','HEAD'):raise ValueError('Curl method')
            elif option in ('-H','--header') and value.startswith('@'):raise ValueError('Header file upload')
            elif option in ('--max-time','--connect-timeout','--max-redirs'):
                if not re.fullmatch(r'\d+(?:\.\d+)?',value) or not 0<float(value)<=300:raise ValueError('Unbounded curl option')
            elif option=='--url':urls.append(value)
            result.extend((option,value))
        elif arg in flags or re.fullmatch(r'-[sSLIfv]+',arg):result.append(arg)
        elif not arg.startswith('-'):urls.append(arg);result.append(arg)
        else:raise ValueError('Curl option needs approval')
    if len(urls)!=1 or any(urlsplit(url).scheme not in ('http','https') or not urlsplit(url).hostname for url in urls):raise ValueError('Use one HTTP(S) URL')
    return result,outputs


def classify_linux(command,exam_dir,resolve_executable,cwd=None):
    """Return a fully validated argv plan, or None for the existing approval flow."""
    try:
        if not isinstance(command,str) or not command.strip() or len(command)>20000 or any(c in command for c in ('\0','\r','\n','`')) or '$(' in command:return None
        root=Path(exam_dir).absolute();_no_redirect(root);root=root.resolve(strict=True)
        current=Path(cwd or os.getcwd()).absolute().resolve(strict=True)
        lexer=shlex.shlex(command,posix=True,punctuation_chars='|&;<>');lexer.whitespace_split=True;lexer.commenters=''
        tokens=list(lexer)
        tokens=[re.sub(r'\$\{CEH_EXAM_DIR\}|\$CEH_EXAM_DIR(?!\w)',lambda _:str(root),value) for value in tokens]
        if any(re.search(r'\$[A-Za-z_{]',token) for token in tokens):return None
        groups=[];group=[];condition=';'
        for token in tokens:
            if token in (';','&&'):
                if not group:return None
                groups.append((condition,group));group=[];condition=token
            elif token in ('&','||','<','<<','<<<','>&','&>',';;'):return None
            else:group.append(token)
        if group:groups.append((condition,group))
        elif tokens and tokens[-1]!=';':return None
        plan=[];writes=set()
        for condition,group in groups:
            output=None;append=False
            redirects=[i for i,t in enumerate(group) if t in ('>','>>')]
            if redirects:
                index=redirects[0]
                if len(redirects)!=1 or index!=len(group)-2 or index==0:return None
                append=group[index]=='>>';output=_output(group[-1],current,root,append);group=group[:index]
                if output in writes and not append:return None
                writes.add(output)
            if group[0]=='cd':
                if len(group)!=2 or output or group[1]=='-' or group[1].startswith('~'):return None
                target=Path(group[1]);target=target if target.is_absolute() else current/target
                if not target.is_dir():return None
                current=target.resolve();plan.append(dict(cd=str(current),condition=condition));continue
            pipeline=[];stage=[]
            for token in [*group,'|']:
                if token=='|':
                    if not stage:return None
                    name=Path(stage[0]).name;args=stage[1:];files=[]
                    if name=='curl':args,files=_curl(args,current,root)
                    elif name=='sort':
                        if not _sort_safe(args):return None
                    elif name=='uniq':
                        if not _uniq_safe(args):return None
                    elif name not in {'pwd','ls','cat','head','tail','wc','id','whoami','uname','ps','df','du','stat','readlink','grep','egrep','fgrep','cut','tr','echo','printf','strings','base64','sha1sum','sha224sum','sha256sum','sha512sum','md5sum','dig','nslookup','whois','which'}:return None
                    executable=resolve_executable(stage[0])
                    if not executable:return None
                    pipeline.append([executable,*args]);stage=[]
                    if files:
                        if output:return None
                        if any(path in writes for path in files):return None
                        writes.update(files)
                else:stage.append(token)
            if not pipeline:return None
            plan.append(dict(argv=pipeline,cwd=str(current),output=output,append=append,condition=condition,root=str(root)))
        return plan or None
    except (ValueError,OSError):return None


def run_linux(plan,run_pipeline):
    results=[];status=0
    for step in plan:
        if step['condition']=='&&' and status:continue
        if 'cd' in step:
            status=0 if Path(step['cd']).is_dir() else 1
            results.append(f'Exit code: {status}, Directory: '+step['cd'])
            if status:break
            continue
        argv=[[arg.replace('$?',str(status)) if Path(stage[0]).name.removesuffix('.exe') in ('echo','printf') else arg for arg in stage] for stage in step['argv']]
        root=Path(step['root']);cwd=Path(step['cwd'])
        try:
            if step['output']:_output(step['output'],cwd,root,step['append'])
            # Revalidate curl output paths immediately before launch too.
            for stage in argv:
                if Path(stage[0]).name.removesuffix('.exe')=='curl':
                    for i,arg in enumerate(stage[:-1]):
                        if arg in ('-o','--output') and stage[i+1]!='-':_output(stage[i+1],cwd,root)
        except (ValueError,OSError):
            results.append('Exit code: 1, Output:\nRoutine workflow stopped: output destination changed or existing evidence would be overwritten. Choose a new result filename; completed steps were not replayed.')
            break
        kwargs=dict(cwd=step['cwd'])
        if step['output']:kwargs.update(stdout_path=step['output'],append=step['append'])
        result=run_pipeline(argv,**kwargs);results.append(result)
        match=re.search(r'Exit code: (-?\d+)',result);status=int(match.group(1)) if match else 1
    return '\n\n'.join(results)
