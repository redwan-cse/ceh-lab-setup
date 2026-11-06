"""Offline tests of setup safety functions, with no imports that run installation."""
import ast
from pathlib import Path
import tempfile
import unittest

# Load only the two pure definitions from the actual installer helper. Importing
# that script normally performs installation, so the AST allowlist is deliberate.
source = Path(__file__).with_name('shellgpt_stepfun_setup.py')
tree = ast.parse(source.read_text(encoding='utf-8'))
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in {'read_saved_key', 'check_environment_conflicts'}]
assert len(selected) == 2
namespace = {}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
read_saved_key = namespace['read_saved_key']
check_environment_conflicts = namespace['check_environment_conflicts']


class SetupSafetyTests(unittest.TestCase):
    def config_result(self, provider, reset=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.sgptrc'
            # Dummy values only. Tests never include their values in assertion output.
            original = 'OPENAI_API_KEY=offline-test-value\n'
            if provider is not None:
                original += 'API_BASE_URL=' + provider + '\n'
            path.write_text(original, encoding='utf-8')
            key, discarded = read_saved_key(path, reset)
            self.assertTrue(path.read_text(encoding='utf-8') == original)
            return bool(key), discarded

    def test_same_provider_preserves_key(self):
        for provider in ('https://api.stepfun.ai/step_plan/v1',
                         'https://api.stepfun.ai/v1', 'https://api.stepfun.ai:443/v1'):
            self.assertEqual(self.config_result(provider), (True, False))

    def test_foreign_missing_or_malformed_provider_drops_key(self):
        for provider in (None, '', 'https://api.openai.com/v1',
                         'https://api.stepfun.ai.attacker.invalid/v1',
                         'https://attacker.invalid/api.stepfun.ai',
                         'http://api.stepfun.ai/v1', 'https://api.stepfun.ai:444/v1',
                         'https://user@api.stepfun.ai/v1', 'https://api.stepfun.ai:bad/v1'):
            self.assertEqual(self.config_result(provider), (False, True))

    def test_explicit_reset_drops_same_provider_key(self):
        self.assertEqual(self.config_result('https://api.stepfun.ai/step_plan/v1', True),
                         (False, False))

    def test_missing_config_has_no_key(self):
        with tempfile.TemporaryDirectory() as directory:
            key, discarded = read_saved_key(Path(directory) / 'missing')
            self.assertFalse(bool(key))
            self.assertFalse(discarded)

    def test_environment_conflicts_refuse_without_values_or_mutation(self):
        names = ('OPENAI_API_KEY', 'API_BASE_URL')
        for environment in ({'OPENAI_API_KEY': 'offline-test-secret'},
                            {'API_BASE_URL': 'https://offline.invalid'}):
            before = environment.copy()
            with self.assertRaises(RuntimeError) as caught:
                check_environment_conflicts(names, environment)
            message = str(caught.exception)
            self.assertTrue(all(value not in message for value in environment.values()))
            self.assertTrue(all(name in message for name in environment))
            self.assertEqual(environment, before)
        check_environment_conflicts(names, {'UNRELATED': 'value'}, {'OPENAI_API_KEY': ''})


if __name__ == '__main__':
    unittest.main()
