from pathlib import Path
import tempfile
import unittest
from reset_exam_logs import reset_logs


class ResetTests(unittest.TestCase):
    def test_only_generated_logs_are_removed_and_findings_survive(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'CEH-Exam';report=root/'10.0.0.2';report.mkdir(parents=True)
            state=Path(folder)/'private-state';(state/'10.0.0.2').mkdir(parents=True)
            for name in ('terminal.txt','commands.txt','commands.log','network-info.json'):(report/name).write_text('test log')
            (report/'findings.txt').write_text('Flag: KEEP\nHow found: actual evidence\n')
            (report/'unrelated.txt').write_text('keep')
            (state/'10.0.0.2/evidence-index.jsonl').write_text('old offsets')
            (state/'10.0.0.2/last-task.json').write_text('{"completed":true}')
            reset_logs(root,state,clear=False)
            self.assertTrue((report/'terminal.txt').exists())
            reset_logs(root,state,clear=True)
            self.assertEqual({p.name for p in report.iterdir()},{'findings.txt','unrelated.txt'})
            self.assertFalse((state/'10.0.0.2/evidence-index.jsonl').exists())
            self.assertFalse((state/'10.0.0.2/last-task.json').exists())
            self.assertIn('KEEP',(report/'findings.txt').read_text())

if __name__=='__main__':unittest.main()
