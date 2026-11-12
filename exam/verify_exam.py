"""Three small billable checks. Run with the exam venv Python after saving a key."""
import os
from pathlib import Path
import subprocess
import sys

path=Path.home()/'.config'/'shell_gpt_exam'/'.sgptrc'
values=dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)
key=values.get('OPENAI_API_KEY','')
if not key:raise SystemExit('Configure the exam key before live tests.')
root=Path(sys.executable).parent.parent
runtime=root.parent/'exam_runtime.py'
command='Get-Location' if os.name=='nt' else 'pwd'
date='Get-Date' if os.name=='nt' else 'date'
tests=[(['--no-cache','--no-functions','Reply exactly EXAM_TEXT_OK'],['EXAM_TEXT_OK']),
       (['--no-cache','--no-functions','--shell',f'Return exactly {command} and nothing else.'],['Automatically running']),
       (['--no-cache',f'Use execute_shell_command exactly once to run {date}. After the tool succeeds reply EXAM_TOOL_OK.'],['Automatically running','EXAM_TOOL_OK'])]
for i,(args,expected) in enumerate(tests,1):
    result=subprocess.run([sys.executable,str(runtime),*args],input='',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360)
    output=(result.stdout+result.stderr).replace(key,'[REDACTED]')
    print(output,flush=True)
    if result.returncode or 'Approval required' in output or any(s not in output for s in expected):raise SystemExit(f'FAIL: live check {i}')
    print(f'PASS: live check {i}',flush=True)
