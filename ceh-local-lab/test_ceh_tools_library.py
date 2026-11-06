from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from ceh_tools_library import extract_library, inventory, long_path, safe_name, verify_library


class ToolsLibraryTests(unittest.TestCase):
    def test_unsafe_paths_and_windows_names_are_rejected(self):
        for value in ('../escape', '/absolute', 'C:/drive', 'dir/../../escape',
                      'dir/NUL.txt', 'dir/file.', 'dir/a:b', 'dir/name '):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_name(value)

    def test_nested_module_path_is_preserved(self):
        self.assertEqual(safe_name('Module 02/tools/file.txt'),
                         ('Module 02', 'tools', 'file.txt'))

    def test_iso_excluded_and_extraction_verified_on_rerun(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'archives'
            source.mkdir()
            with zipfile.ZipFile(source / 'module.zip', 'w') as z:
                z.writestr('Module/file.txt', 'benign offline fixture')
                z.writestr('Module/embedded.zip', b'preserve nested archive')
            (source / 'CEHv13 ISO.zip').write_bytes(b'not even a valid ZIP')
            manifest = inventory(source)
            self.assertEqual(len(manifest['archives']), 1)
            target = root / 'library'
            extract_library(source, target, manifest)
            self.assertTrue(verify_library(target, manifest))
            self.assertEqual((target / 'Module/embedded.zip').read_bytes(),
                             b'preserve nested archive')
            (target / 'Module/file.txt').write_text('changed', encoding='utf-8')
            self.assertFalse(verify_library(target, manifest))

    def test_conflicting_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'archives'
            source.mkdir()
            with zipfile.ZipFile(source / 'module.zip', 'w') as z:
                z.writestr('file.txt', 'new')
            target = root / 'library'
            target.mkdir()
            (target / 'existing.txt').write_text('keep', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                extract_library(source, target, inventory(source))
            self.assertEqual((target / 'existing.txt').read_text(), 'keep')

    def test_case_collisions_are_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with zipfile.ZipFile(root / 'module.zip', 'w') as z:
                z.writestr('Folder/one.txt', 'one')
                z.writestr('folder/ONE.txt', 'two')
            with self.assertRaises(ValueError):
                inventory(root)

    def test_paths_longer_than_260_characters(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            name = '/'.join(['module'] + ['x' * 90] * 3 + ['readme.txt'])
            with zipfile.ZipFile(root / 'module.zip', 'w') as z:
                z.writestr(name, 'long-path fixture')
            manifest = inventory(root)
            target = root / 'library'
            try:
                extract_library(root, target, manifest)
                self.assertTrue(verify_library(target, manifest))
            finally:
                if target.exists():
                    shutil.rmtree(long_path(target))


if __name__ == '__main__':
    unittest.main()
