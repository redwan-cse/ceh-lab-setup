from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import exam_workflow
import setup_exam


class ReferenceTests(unittest.TestCase):
    def test_bundled_tool_queries_return_recipes_before_inventory(self):
        for query,command in (('nmap','nmap -sT -sV'),('sqlmap','sqlmap -u'),('hashing','sha256sum evidence.bin')):
            with self.subTest(query=query):
                result=exam_workflow.find_reference(query)
                self.assertIn(command,result)
                self.assertLessEqual(len(result),5000)

    def test_lookup_is_bounded_and_does_not_execute_reference_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'network.md').write_text('# Network\n## Nmap\nnmap -sV HOST\n'+'example '*2000)
            (root/'crypto.md').write_text('## Hashing\nsha256sum file\n')
            with patch('exam_workflow.reference_root',return_value=root):
                text=exam_workflow.find_reference('nmap')
                self.assertLessEqual(len(text),5000)
                self.assertIn('Source: network.md',text)
                self.assertNotIn('Source: crypto.md',text)
                self.assertIn('No reference match',exam_workflow.find_reference('unknown-tool'))

    def test_only_canonical_wrapper_reads_active_config(self):
        import os
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'install';root.mkdir()
            with patch.object(setup_exam,'ROOT',root),patch.object(setup_exam.Path,'home',return_value=Path(folder)):
                bindir=setup_exam.write_wrappers('openrouter-deepseek',True,True)
                suffix='.cmd' if os.name=='nt' else ''
                wrapper=(bindir/('sgpt'+suffix)).read_text()
                self.assertNotIn('--profile',wrapper)
                self.assertIn('Launch-Sgpt.ps1' if os.name=='nt' else 'launch-sgpt.sh',wrapper)
                self.assertFalse((bindir/('sgpt-lab'+suffix)).exists())
                self.assertFalse((bindir/('sgpt-exam'+suffix)).exists())

    def test_reference_copy_uses_only_markdown(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);resources=root/'kit/exam';resources.mkdir(parents=True)
            docs=root/'kit/docs/ceh-tools';docs.mkdir(parents=True)
            (docs/'guide.md').write_text('## Tool\nExample')
            (docs/'secret.key').write_text('not copied')
            install=root/'install';install.mkdir()
            with patch.object(setup_exam,'ROOT',install):setup_exam.copy_references(resources)
            self.assertEqual([p.name for p in (install/'references').iterdir()],['guide.md'])


if __name__=='__main__':unittest.main()
