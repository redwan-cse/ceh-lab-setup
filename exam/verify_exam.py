"""Three small billable local checks through the installed sgpt launcher."""
import base64
import os
from pathlib import Path
import re
import subprocess


def live_cases(windows):
    location='Get-Location' if windows else 'pwd'
    date='Get-Date' if windows else 'date'
    return [
        dict(name='text',args=['--no-cache','--no-functions','Reply exactly EXAM_TEXT_OK'],expected='EXAM_TEXT_OK',command=None),
        dict(name='shell',args=['--no-cache','--no-functions','--shell',f'Return exactly {location} and nothing else.'],expected='',command=location),
        dict(name='tool',args=['--no-cache',f'Use execute_shell_command exactly once to run {date}. After the tool succeeds reply EXAM_TOOL_OK.'],expected='EXAM_TOOL_OK',command=date),
    ]


def case_passed(returncode,output,case):
    output=output.replace('\r\n','\n')
    if returncode:return False
    if case['expected'] and not re.search(r'^'+re.escape(case['expected'])+r'\s*$',output,re.M):return False
    if 'Execute this exact command?' in output or '[sgpt] Approval required:' in output:return False
    if case['command']:
        commands=re.findall(r'^COMMAND: (.+)$',output,re.M)
        if commands!=[case['command']]:return False
        if not re.search(r'\bExit code: 0(?:,|\s|$)',output):return False
    return True


def launcher(root,args):
    if os.name=='nt':
        quote=lambda value:"'"+str(value).replace("'","''")+"'"
        code="$ProgressPreference='SilentlyContinue'; & "+quote(root/'bin/sgpt.cmd')+' '+' '.join(quote(arg) for arg in args)+'; exit $LASTEXITCODE'
        encoded=base64.b64encode(code.encode('utf-16le')).decode()
        powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        return [str(powershell),'-NoProfile','-EncodedCommand',encoded]
    return [str(Path.home()/'.local/bin/sgpt'),*args]


def main():
    from setup_exam import ROOT,load_keys,read
    values=read()
    if not values.get('OPENAI_API_KEY'):raise SystemExit('Configure the exam key before live tests.')
    secrets=[value for value in [*load_keys().values(),values.get('OPENAI_API_KEY')] if isinstance(value,str) and value]
    # Filing only: all three commands inspect the local machine, with no scan.
    common=['--challenge','validation-smoke','--target-ip','127.0.0.1']
    for case in live_cases(os.name=='nt'):
        try:
            result=subprocess.run(launcher(ROOT,[*common,*case['args']]),input='',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=190)
        except subprocess.TimeoutExpired:raise SystemExit('FAIL: live check '+case['name']+' timed out; no automatic retry.') from None
        output=result.stdout+result.stderr
        for secret in secrets:output=output.replace(secret,'[REDACTED]')
        print(output,flush=True)
        if not case_passed(result.returncode,output,case):raise SystemExit('FAIL: live check '+case['name'])
        print('PASS: live check '+case['name'],flush=True)


if __name__=='__main__':main()
