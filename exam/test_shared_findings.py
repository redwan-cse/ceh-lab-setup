"""Tests for multiline findings formatting and the cross-session shared findings board."""
import json
from pathlib import Path
import tempfile
import unittest

from exam_workflow import Workflow


class SharedFindingsTests(unittest.TestCase):
    def test_multiline_how_found_preserves_numbered_steps_in_findings_txt(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Workflow(Path(folder), session=True, challenge='1')
            w.execute('cat flag.txt', lambda _: 'Exit code: 0\nFLAG_MULTI_123')
            steps = (
                '1. Enumerated SMB shares on 10.10.10.22\n'
                '2. Downloaded flag.txt from shared folder\n'
                '3. Verified SHA256 and read FLAG_MULTI_123'
            )
            w.finding('FLAG_MULTI_123', steps)
            content = w.findings.read_text(encoding='utf-8')
            expected = (
                'Flag: FLAG_MULTI_123\n'
                'How found:\n'
                '1. Enumerated SMB shares on 10.10.10.22\n'
                '2. Downloaded flag.txt from shared folder\n'
                '3. Verified SHA256 and read FLAG_MULTI_123\n\n'
            )
            self.assertEqual(content, expected)

    def test_shared_findings_board_aggregates_across_challenges_and_injects_into_context(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            c1 = Workflow(root, session=True, challenge='1', target_ip='10.10.10.13')
            c2 = Workflow(root, session=True, challenge='2', target_ip='10.10.10.13')

            c1.execute('id', lambda _: 'Exit code: 0\nFLAG_CHALLENGE_1')
            c1.finding('FLAG_CHALLENGE_1', '1. Ran id\n2. Confirmed output')

            c2.execute('whoami', lambda _: 'Exit code: 0\nFLAG_CHALLENGE_2')
            c2.finding('FLAG_CHALLENGE_2', 'Found via whoami on target')

            # Per-session findings.txt remain isolated
            self.assertIn('FLAG_CHALLENGE_1', c1.findings.read_text(encoding='utf-8'))
            self.assertNotIn('FLAG_CHALLENGE_2', c1.findings.read_text(encoding='utf-8'))
            self.assertIn('FLAG_CHALLENGE_2', c2.findings.read_text(encoding='utf-8'))

            # Shared findings board has both with provenance
            c3 = Workflow(root, session=True, challenge='3', target_ip='10.10.10.13')
            shared = c3.shared_findings()
            self.assertEqual([item['flag'] for item in shared], ['FLAG_CHALLENGE_1', 'FLAG_CHALLENGE_2'])
            self.assertEqual(shared[0]['challenge'], 'challenge-1')
            self.assertEqual(shared[1]['challenge'], 'challenge-2')
            self.assertIn('1. Ran id\n2. Confirmed output', shared[0]['how_found'])

            board_md = (root / 'shared-findings.md').read_text(encoding='utf-8')
            self.assertIn('FLAG_CHALLENGE_1', board_md)
            self.assertIn('FLAG_CHALLENGE_2', board_md)
            self.assertIn('challenge-1', board_md)
            self.assertIn('1. Ran id\n2. Confirmed output', board_md)

            # New session's context automatically includes confirmed shared findings
            self.assertIn('FLAG_CHALLENGE_1', c3.context())
            self.assertIn('FLAG_CHALLENGE_2', c3.context())


if __name__ == '__main__':
    unittest.main()
