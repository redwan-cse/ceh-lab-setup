"""Three processes preserve output offsets and script ownership without API calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from exam_workflow import Workflow


WORKER=r'''
import json,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from exam_workflow import Workflow
from lab_scripts import LabScripts
root=Path(sys.argv[2]);tag=sys.argv[3]
w=Workflow.__new__(Workflow);w.folder=root;w.state=root/'.state';w.log=root/'terminal.md';w.findings=root/'findings.txt';w.secret='';w.recent_evidence=[];w.original_stream=None
original=Path.open
class SlowTell:
    def __init__(self,stream):self.stream=stream
    def __enter__(self):return self
    def __exit__(self,*args):return self.stream.__exit__(*args)
    def __getattr__(self,name):return getattr(self.stream,name)
    def tell(self):
        value=self.stream.tell();time.sleep(0.005);return value
def opened(path,mode='r',*args,**kwargs):
    stream=original(path,mode,*args,**kwargs)
    return SlowTell(stream) if path.name=='terminal.md' and mode=='ab' else stream
Path.open=opened
for index in range(10):
    text=tag+':'+str(index)+':'+'x'*1024+'\n'
    start,end=w.append(w.log,text)
    w.append(w.state/'parallel-index.jsonl',json.dumps(dict(start=start,end=end,text=text))+'\n')
    w.write('parallel-last.json',json.dumps(dict(worker=tag,index=index)))
scripts=LabScripts(w)
for index in range(3):scripts.write('parallel','python','print('+repr(tag+str(index))+')')
'''


class ParallelStateTests(unittest.TestCase):
    def test_three_terminal_processes_keep_output_offsets_and_all_scripts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);Workflow(root)
            source=root/'worker.py';source.write_text(WORKER)
            processes=[subprocess.Popen([sys.executable,str(source),str(Path(__file__).parent),str(root),str(tag)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for tag in range(3)]
            for process in processes:
                out,err=process.communicate(timeout=30)
                self.assertEqual(process.returncode,0,out+err)
            records=[json.loads(line) for line in (root/'.state/parallel-index.jsonl').read_text().splitlines()]
            self.assertEqual(len(records),30)
            data=(root/'terminal.md').read_bytes()
            for record in records:self.assertEqual(data[record['start']:record['end']].decode(),record['text'])
            scripts=json.loads((root/'.state/scripts-index.json').read_text())
            self.assertEqual(len(scripts),9)
            self.assertEqual(len(list((root/'scripts').glob('scripts_parallel_*.py'))),9)
            self.assertIn(json.loads((root/'.state/parallel-last.json').read_text())['worker'],('0','1','2'))


if __name__=='__main__':unittest.main()
