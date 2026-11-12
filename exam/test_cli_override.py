"""Existing user launchers survive exam setup, repair and removal."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import setup_exam
import uninstall_exam


class CliOverrideTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / 'install'
        self.root.mkdir()
        self.bin = self.root / 'bin' if os.name == 'nt' else self.home / '.local/bin'
        self.bin.mkdir(parents=True)
        self.name = 'sgpt.cmd' if os.name == 'nt' else 'sgpt'
        self.command = self.bin / self.name
        self.runtime = str(self.root / 'exam_runtime.py')
        (self.root / 'exam_runtime.py').write_text('"""ShellGPT exam entry point."""\n')
        for module in (setup_exam, uninstall_exam):
            mocked = patch.object(module, 'ROOT', self.root)
            mocked.start()
            self.addCleanup(mocked.stop)
        mocked = patch.object(setup_exam.Path, 'home', return_value=self.home)
        mocked.start()
        self.addCleanup(mocked.stop)
        # ACLs are independently covered; these fixtures never use a real profile.
        mocked = patch.object(setup_exam, 'windows_acl')
        mocked.start()
        self.addCleanup(mocked.stop)

    def backups(self):
        return list(self.bin.glob(self.name + '.before-exam*'))

    def install(self):
        return setup_exam.write_wrappers()

    def restore(self):
        backup = setup_exam.load_cli_backup(self.bin, self.command)
        uninstall_exam.clean_wrapper(self.command, self.runtime, backup=backup)

    def test_regular_user_launcher_is_backed_up_once_and_restored(self):
        self.command.write_bytes(b'original universal launcher\r\n')
        global_command = self.home / 'global-sgpt'
        global_command.write_bytes(b'global package untouched')
        self.install()
        first = self.backups()
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].read_bytes(), b'original universal launcher\r\n')
        self.assertIn(self.runtime, self.command.read_text())
        self.install()
        self.assertEqual(self.backups(), first)
        self.restore()
        self.assertEqual(self.command.read_bytes(), b'original universal launcher\r\n')
        self.assertEqual(global_command.read_bytes(), b'global package untouched')
        self.assertFalse(first[0].exists())

    def test_older_backups_are_preserved_and_selected_backup_is_restored(self):
        previous = self.bin / (self.name + '.before-exam')
        previous.write_text('older backup')
        self.command.write_text('current original')
        self.install()
        self.assertEqual(len(self.backups()), 2)
        self.restore()
        self.assertEqual(self.command.read_text(), 'current original')
        self.assertEqual(previous.read_text(), 'older backup')

    def symlink(self, path, target):
        try:
            path.symlink_to(target)
        except OSError as error:
            self.skipTest('Symbolic links unavailable: ' + str(error))

    def test_pipx_link_itself_is_moved_and_restored_without_changing_target(self):
        package = self.home / 'pipx-sgpt'
        package.write_bytes(b'pipx executable untouched')
        self.symlink(self.command, package)
        original_link = os.readlink(self.command)
        self.install()
        backup = self.backups()[0]
        self.assertTrue(backup.is_symlink())
        self.assertEqual(os.readlink(backup), original_link)
        self.assertFalse(self.command.is_symlink())
        self.assertEqual(package.read_bytes(), b'pipx executable untouched')
        self.restore()
        self.assertTrue(self.command.is_symlink())
        self.assertEqual(os.readlink(self.command), original_link)
        self.assertEqual(package.read_bytes(), b'pipx executable untouched')

    def test_broken_pipx_link_can_be_restored(self):
        missing = self.home / 'missing-pipx-command'
        self.symlink(self.command, missing)
        original_link = os.readlink(self.command)
        self.install()
        self.restore()
        self.assertTrue(self.command.is_symlink())
        self.assertEqual(os.readlink(self.command), original_link)

    def test_unmanaged_legacy_aliases_are_left_alone(self):
        suffix = '.cmd' if os.name == 'nt' else ''
        aliases = [self.bin / (name + suffix) for name in ('sgpt-exam', 'sgpt-lab')]
        for path in aliases:
            path.write_text('unrelated alias')
        self.install()
        for path in aliases:
            self.assertEqual(path.read_text(), 'unrelated alias')

    def test_manifest_failure_restores_original_before_raising(self):
        self.command.write_text('keep original')
        with patch.object(setup_exam, 'atomic_private_write', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.install()
        self.assertEqual(self.command.read_text(), 'keep original')
        self.assertEqual(self.backups(), [])

    def test_wrapper_failure_keeps_recoverable_original(self):
        self.command.write_text('keep original')
        original_write = setup_exam.atomic_private_write

        def fail_wrapper(path, text):
            if path == self.command:
                raise OSError('cannot write wrapper')
            return original_write(path, text)

        with patch.object(setup_exam, 'atomic_private_write', side_effect=fail_wrapper):
            with self.assertRaises(OSError):
                self.install()
        self.assertEqual(self.command.read_text(), 'keep original')
        self.assertEqual(self.backups(), [])

    def test_failed_setup_rollback_preserves_original_for_manual_recovery(self):
        self.command.write_text('irreplaceable original')
        original_write = setup_exam.atomic_private_write
        original_replace = os.replace

        def fail_wrapper(path, text):
            if path == self.command:
                raise OSError('cannot write wrapper')
            return original_write(path, text)

        def fail_restore(source, destination):
            if Path(destination) == self.command:
                raise OSError('cannot restore wrapper')
            return original_replace(source, destination)

        with patch.object(setup_exam, 'atomic_private_write', side_effect=fail_wrapper), \
                patch.object(setup_exam.os, 'replace', side_effect=fail_restore):
            with self.assertRaisesRegex(RuntimeError, 'preserved'):
                self.install()
        self.assertEqual(self.backups()[0].read_text(), 'irreplaceable original')
        # The saved selection also allows a later setup to finish safely.
        self.install()
        self.restore()
        self.assertEqual(self.command.read_text(), 'irreplaceable original')

    def test_manifest_cannot_restore_an_outside_file(self):
        self.command.write_text('original')
        self.install()
        manifest = self.root / 'cli-backup.json'
        record = json.loads(manifest.read_text())
        outside = self.home / 'outside.before-exam'
        outside.write_text('outside protected')
        record['backupPath'] = str(outside)
        manifest.write_text(json.dumps(record))
        before = self.command.read_bytes()
        with self.assertRaises(RuntimeError):
            self.restore()
        self.assertEqual(self.command.read_bytes(), before)
        self.assertEqual(outside.read_text(), 'outside protected')

    def test_restore_failure_preserves_wrapper_and_original_backup(self):
        self.command.write_text('original')
        self.install()
        backup = self.backups()[0]
        before = self.command.read_bytes()
        with patch.object(uninstall_exam.os, 'replace', side_effect=OSError('access denied')):
            with self.assertRaises(OSError):
                self.restore()
        self.assertEqual(self.command.read_bytes(), before)
        self.assertEqual(backup.read_text(), 'original')

    def test_redirected_bin_directory_is_refused(self):
        self.bin.rmdir()
        outside = self.home / 'external-bin'
        outside.mkdir()
        self.symlink(self.bin, outside)
        with self.assertRaises(RuntimeError):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])

    def test_full_uninstall_retains_restored_launcher_and_unrelated_alias(self):
        self.command.write_text('original user command')
        alias = self.bin / ('sgpt-lab.cmd' if os.name == 'nt' else 'sgpt-lab')
        alias.write_text('unrelated alias')
        self.install()
        registry = MagicMock()
        registry.QueryValueEx.return_value = (str(self.bin), 2)
        with patch.object(uninstall_exam, 'CONFIG', self.home / 'absent-config'), \
                patch('sys.argv', ['uninstall_exam.py', '--keep-config']), \
                patch.dict('sys.modules', {'winreg': registry}):
            uninstall_exam.main()
        self.assertEqual(self.command.read_text(), 'original user command')
        self.assertEqual(alias.read_text(), 'unrelated alias')
        self.assertFalse((self.root / 'exam_runtime.py').exists())

    def test_uninstall_handles_an_already_missing_bin_directory(self):
        self.bin.rmdir()
        registry = MagicMock()
        registry.QueryValueEx.return_value = (str(self.bin), 2)
        with patch.object(uninstall_exam, 'CONFIG', self.home / 'absent-config'), \
                patch('sys.argv', ['uninstall_exam.py', '--keep-config']), \
                patch.dict('sys.modules', {'winreg': registry}):
            uninstall_exam.main()
        self.assertFalse(self.root.exists())


if __name__ == '__main__':
    unittest.main()
