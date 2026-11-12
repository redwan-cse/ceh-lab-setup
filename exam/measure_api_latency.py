"""Interleaved real sgpt short-response timings; paid calls, no tools."""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from setup_exam import ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats',type=int,default=3)
    args=parser.parse_args()
    if not 1<=args.repeats<=5:raise ValueError('Choose 1–5 repetitions')
    results=[]
    for i in range(args.repeats):
        profiles=['openrouter-deepseek','stepfun'] if i%2==0 else ['stepfun','openrouter-deepseek']
        for profile in profiles:
            start=time.monotonic()
            result=subprocess.run([sys.executable,str(ROOT/'exam_runtime.py'),'--profile',profile,'--no-functions','Reply exactly LATENCY_READY and nothing else.'],input='',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=110,env=dict(os.environ,PYTHONIOENCODING='utf-8'))
            output=result.stdout+result.stderr
            api=[]
            for match in re.finditer(r'\[API\] (\{[^\r\n]+\})',output):
                api.append(json.loads(match.group(1)))
            record=dict(profile=profile,trial=i+1,passed=result.returncode==0 and len(api)==1 and api[0].get('status')=='returned' and 'LATENCY_READY' in output.rsplit('[API]',1)[-1] and 'no usable completion' not in output,api_seconds=api[0]['seconds'] if len(api)==1 else None,cli_seconds=round(time.monotonic()-start,3))
            results.append(record);print('LATENCY_TRIAL '+json.dumps(record),flush=True)
    summary=[]
    for profile in ('openrouter-deepseek','stepfun'):
        times=[r['api_seconds'] for r in results if r['profile']==profile and r['passed']]
        summary.append(dict(profile=profile,passed=len(times),trials=args.repeats,median_api_seconds=statistics.median(times) if times else None,mean_api_seconds=statistics.mean(times) if times else None))
    print('LATENCY_SUMMARY '+json.dumps(summary),flush=True)

if __name__=='__main__':main()
