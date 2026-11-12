from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from exam_workflow import Workflow


def workflow(root):
    w=Workflow.__new__(Workflow);w.state=root/'state';w.state.mkdir()
    w.folder=root/'report';w.folder.mkdir();w.secret='';w.recent_evidence=[]
    return w


class OptionalToolsTests(unittest.TestCase):
    def test_path_tool_is_found_without_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);w=workflow(root);tool=root/'nmap';tool.touch()
            with patch('exam_workflow.shutil.which',return_value=str(tool)),patch('exam_workflow.desktop',return_value=root/'Desktop'):
                result=w.find_tools('nmap')
            self.assertIn(str(tool),result)
            self.assertNotIn('Ask Redwan',result)

    def test_desktop_wordlist_is_found_without_custom_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);w=workflow(root);lists=root/'Desktop/Lab Wordlists';lists.mkdir(parents=True)
            wordlist=lists/'small-list.txt';wordlist.write_text('fixture')
            with patch('exam_workflow.shutil.which',return_value=None),patch('exam_workflow.desktop',return_value=root/'Desktop'):
                self.assertIn(str(wordlist),w.find_tools('wordlists'))

    def test_missing_optional_catalog_never_demands_initialization(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);w=workflow(root)
            with patch('exam_workflow.shutil.which',return_value=None),patch('exam_workflow.desktop',return_value=root/'Desktop'):
                result=w.find_tools('missing-tool')
            self.assertNotIn('initialize with',result)
            self.assertNotIn('Ask Redwan',result)

    def test_current_directory_file_is_found_without_custom_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);w=workflow(root);work=root/'work';work.mkdir()
            item=work/'passwords.txt';item.write_text('fixture')
            with patch('exam_workflow.shutil.which',return_value=None),patch('exam_workflow.desktop',return_value=root/'Desktop'),patch('exam_workflow.Path.cwd',return_value=work):
                self.assertIn(str(item),w.find_tools('passwords.txt'))

    def test_user_can_supply_optional_path_in_chat(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);w=workflow(root);tools=root/'Provided Tools';tools.mkdir()
            item=tools/'emt.exe';item.write_text('not executed')
            result=w.set_tools_path(str(tools),user_text='Use "'+str(tools)+'" for this task')
            self.assertIn('Optional',result)
            with patch('exam_workflow.shutil.which',return_value=None),patch('exam_workflow.desktop',return_value=root/'Desktop'):
                self.assertIn(str(item),w.find_tools('emt'))

    def test_model_cannot_set_a_path_user_never_supplied(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);w=workflow(root)
            with self.assertRaises(ValueError):w.set_tools_path(str(root),user_text='Hello')


if __name__=='__main__':unittest.main()
