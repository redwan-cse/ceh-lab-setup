from pathlib import Path
import tempfile
import unittest
from uninstall_exam import clean_wrapper, remove_tree


class RemovalTests(unittest.TestCase):
    def test_owned_wrapper_restores_previous_command(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sgpt'
            path.write_text('python /home/test/shellgpt-exam/exam_runtime.py')
            backup=path.with_name('sgpt.before-exam');backup.write_text('original command')
            clean_wrapper(path,'/home/test/shellgpt-exam/exam_runtime.py')
            self.assertEqual(path.read_text(),'original command')
            self.assertFalse(backup.exists())

    def test_unrelated_wrapper_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sgpt';path.write_text('another command')
            with self.assertRaises(RuntimeError):clean_wrapper(path,'our runtime')
            self.assertEqual(path.read_text(),'another command')

    def test_tree_outside_allowed_parent_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            parent=Path(folder)
            with self.assertRaises(RuntimeError):remove_tree(parent,parent/'allowed')
            self.assertTrue(parent.exists())

    def test_dry_run_preserves_files(self):
        with tempfile.TemporaryDirectory() as folder:
            parent=Path(folder);target=parent/'shellgpt-exam';target.mkdir()
            (target/'fixture').write_text('test')
            remove_tree(target,parent,dry_run=True)
            self.assertTrue(target.exists())
            remove_tree(target,parent)
            self.assertFalse(target.exists())

if __name__=='__main__':unittest.main()
