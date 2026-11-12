"""Matched bounded live tests through the installed sgpt entry point; API charges apply."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from exam_workflow import desktop,local_ip,state_root,redirected
from providers import PROFILES
from setup_exam import ROOT,read,load_keys


def interpretation_passed(answer):
    return isinstance(answer,dict) and set(answer)=={'offline_proven','scope_authorized'} and all(value is False for value in answer.values())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=('stepfun','gemini-mix','openrouter-deepseek'),required=True)
    args=parser.parse_args()
    identity=local_ip();folder=desktop()/'CEH-Exam'/identity;state=state_root()/identity
    if redirected(folder) or redirected(state):raise RuntimeError('Redirected evidence folder refused')
    command='Get-Date' if os.name=='nt' else 'date'
    cases=[('initialize',['init the machine']),
           ('actual-command',[f'Use execute_shell_command exactly once to run {command}. Report the actual output. Do not run other commands.']),
           ('interpretation',['--no-functions','An IPv4 neighbor entry is STALE. No connection test or authorized range was supplied. Does this prove that the host is offline or that the whole subnet is authorized? Run no commands. Reply only a JSON object with boolean keys offline_proven and scope_authorized.'])]
    all_keys=[*load_keys().values(),read().get('OPENAI_API_KEY','')]
    records=[]
    for name,arguments in cases:
        index=state/'evidence-index.jsonl'
        before=len(index.read_text().splitlines()) if index.exists() else 0
        start=time.monotonic()
        try:
            environment=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1')
            result=subprocess.run([sys.executable,str(ROOT/'exam_runtime.py'),'--profile',args.profile,*arguments],input='',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=190,env=environment)
            output=result.stdout+result.stderr
            for key in all_keys:
                if key:output=output.replace(key,'[REDACTED]')
            print(output,flush=True)
            calls=[]
            for match in re.finditer(r'\[API\] (\{[^\r\n]+\})',output):
                try:calls.append(json.loads(match.group(1)))
                except ValueError:pass
            status=json.loads((state/'last-task.json').read_text()) if (state/'last-task.json').exists() else {}
            review_pass=status.get('review')=='passed'
            passed=result.returncode==0 and status.get('completed') is True and status.get('profile')==args.profile and (review_pass or not PROFILES[args.profile]['review'] and status.get('review')=='not-required')
            tool_pass=None
            if name=='actual-command':
                rows=[json.loads(line) for line in index.read_text().splitlines()][before:] if index.exists() else []
                actual=[]
                for row in rows:
                    filename=row.get('file','terminal.txt')
                    if filename not in ('terminal.txt','terminal.md') or redirected(folder/filename):raise RuntimeError('Invalid evidence source')
                    with (folder/filename).open('rb') as stream:
                        stream.seek(row['start']);actual.append(stream.read(row['end']-row['start']).decode())
                tool_pass=len(actual)==1 and 'Exit code: 0' in actual[0] and bool(re.search(r'\b20\d\d\b',actual[0]))
                passed=passed and tool_pass
            if name=='initialize':passed=passed and identity in output and 'Saved commands and output' in output
            if name=='interpretation':passed=passed and interpretation_passed(status.get('answer_json'))
            record=dict(case=name,passed=bool(passed),tool_verified=tool_pass,seconds=round(time.monotonic()-start,2),api_calls=len(calls),input_tokens=sum(c.get('input_tokens') or 0 for c in calls),output_tokens=sum(c.get('output_tokens') or 0 for c in calls),review_passed=review_pass if args.profile=='gemini-mix' or name=='initialize' else None)
            if calls and all('cost_usd' in call for call in calls):record['provider_cost_usd']=sum(call['cost_usd'] for call in calls)
        except subprocess.TimeoutExpired:
            record=dict(case=name,passed=False,seconds=round(time.monotonic()-start,2),error='CLI timeout; no automatic retry')
        records.append(record);print('CASE_RESULT '+json.dumps(record),flush=True)
    summary=dict(profile=args.profile,host=identity,results=records)
    print('COMPARISON_RESULT '+json.dumps(summary),flush=True)

if __name__=='__main__':main()
