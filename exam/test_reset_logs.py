from pathlib import Path
import tempfile
import unittest
from reset_exam_logs import reset_logs


class ResetTests(unittest.TestCase):
    def test_session_logs_reset_preserves_findings_scripts_and_other_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'CEH-Exam';report=root/'10.0.0.2/sessions/challenge-5_fixture';report.mkdir(parents=True)
            state=Path(folder)/'private-state';internal=state/'10.0.0.2/sessions/challenge-5_fixture';internal.mkdir(parents=True)
            (report/'terminal.md').write_text('generated transcript')
            (report/'findings.txt').write_text('Flag: KEEP\nHow found: real output\n')
            (report/'result.txt').write_text('keep report')
            (internal/'evidence-index.jsonl').write_text('offsets')
            (internal/'scripts-index.json').write_text('{}')
            reset_logs(root,state,clear=False)
            self.assertTrue((report/'terminal.md').exists())
            reset_logs(root,state,clear=True)
            self.assertFalse((report/'terminal.md').exists())
            self.assertFalse((internal/'evidence-index.jsonl').exists())
            self.assertTrue((internal/'scripts-index.json').exists())
            self.assertIn('KEEP',(report/'findings.txt').read_text())
            self.assertEqual((report/'result.txt').read_text(),'keep report')

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
