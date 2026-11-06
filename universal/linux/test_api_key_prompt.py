"""Check credential updates using temporary files and dummy values only."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io

from prompt_api_key import main, save_key


class ApiKeyPromptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / '.sgptrc'
        self.original = ('OPENAI_API_KEY=dummy-existing\n'
                         'API_BASE_URL=https://api.stepfun.ai/step_plan/v1\n'
                         'REASONING_EFFORT=high\n')
        self.path.write_text(self.original, encoding='utf-8')

    def test_replace_preserves_settings_and_private_mode(self):
        self.assertTrue(save_key(self.path, 'dummy-replacement'))
        self.assertEqual(self.path.read_text(encoding='utf-8'),
                         self.original.replace('dummy-existing', 'dummy-replacement'))
        if os.name != 'nt':
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_blank_keeps_existing_key(self):
        self.assertFalse(save_key(self.path, ''))
        self.assertEqual(self.path.read_text(encoding='utf-8'), self.original)

    def test_multiline_key_is_rejected_without_changes(self):
        for value in ('dummy\nINJECTED=value', 'dummy\rvalue'):
            with self.assertRaises(ValueError):
                save_key(self.path, value)
        self.assertEqual(self.path.read_text(encoding='utf-8'), self.original)

    def test_foreign_provider_is_rejected_without_changes(self):
        foreign = self.original.replace('api.stepfun.ai', 'api.openai.com')
        self.path.write_text(foreign, encoding='utf-8')
        with self.assertRaises(ValueError):
            save_key(self.path, 'dummy-replacement')
        self.assertEqual(self.path.read_text(encoding='utf-8'), foreign)

    def test_interactive_prompt_saves_without_printing_key(self):
        with patch('prompt_api_key.sys.stdin.isatty', return_value=True), \
             patch('prompt_api_key.Path.home', return_value=Path(self.temp.name)), \
             patch('prompt_api_key.getpass.getpass', return_value='dummy-hidden') as prompt, \
             patch('prompt_api_key.sys.stdout', new_callable=io.StringIO) as output:
            config = Path(self.temp.name) / '.config' / 'shell_gpt' / '.sgptrc'
            config.parent.mkdir(parents=True)
            config.write_text(self.original, encoding='utf-8')
            main()
            prompt.assert_called_once()
            self.assertIn('OPENAI_API_KEY=dummy-hidden', config.read_text(encoding='utf-8'))
            self.assertNotIn('dummy-hidden', output.getvalue())

    def test_noninteractive_run_skips_prompt_and_configuration(self):
        with patch('prompt_api_key.sys.stdin.isatty', return_value=False), \
             patch('prompt_api_key.getpass.getpass') as prompt, \
             patch('prompt_api_key.sys.stdout', new_callable=io.StringIO):
            main()
            prompt.assert_not_called()

    @unittest.skipIf(os.name == 'nt', 'Linux symlink behavior')
    def test_redirected_config_is_rejected(self):
        link = self.path.with_name('redirected')
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            save_key(link, 'dummy-replacement')
        self.assertEqual(self.path.read_text(encoding='utf-8'), self.original)


if __name__ == '__main__':
    unittest.main()
