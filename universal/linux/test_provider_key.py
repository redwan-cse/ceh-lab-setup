"""Exercise the pure provider/key rule without running the installer."""
import ast
from pathlib import Path
import unittest
from urllib.parse import urlsplit

source = ast.parse(Path(__file__).with_name('configure_shellgpt.py').read_text(encoding='utf-8'))
function = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == 'preserved_stepfun_key')
namespace = {'urlsplit': urlsplit}
exec(compile(ast.Module(body=[function], type_ignores=[]), '<provider-key-policy>', 'exec'), namespace)
preserve = namespace['preserved_stepfun_key']


class ProviderKeyTests(unittest.TestCase):
    def test_same_provider_key_is_preserved(self):
        for base in ('https://api.stepfun.ai/step_plan/v1', 'https://api.stepfun.ai:443/v1'):
            self.assertEqual(preserve({'API_BASE_URL':base, 'OPENAI_API_KEY':'dummy-stepfun-key'}), 'dummy-stepfun-key')

    def test_foreign_or_ambiguous_provider_is_not_reused(self):
        for base in ('https://api.openai.com/v1', '', 'http://api.stepfun.ai/v1',
                     'https://api.stepfun.ai.evil.example/v1', 'https://user@api.stepfun.ai/v1',
                     'https://api.stepfun.ai:444/v1', 'https://api.stepfun.ai:invalid/v1'):
            with self.subTest(base=base):
                self.assertEqual(preserve({'API_BASE_URL':base, 'OPENAI_API_KEY':'dummy-foreign-key'}), '')


if __name__ == '__main__':
    unittest.main()
