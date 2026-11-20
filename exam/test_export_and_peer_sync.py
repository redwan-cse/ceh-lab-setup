"""Tests for durable evidence bundle export and Windows <-> Parrot peer findings sync."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

from exam_workflow import Workflow


class ExportAndPeerSyncTests(unittest.TestCase):
    def test_export_evidence_bundles_transcripts_findings_scripts_and_redacts_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Simulate a stray secret file in root to verify secrets are excluded
            (root / '.sgptrc').write_text('OPENAI_API_KEY=super-secret-key-123\n', encoding='utf-8')
            (root / 'provider-keys.json').write_text('{"openrouter":"super-secret-key-123"}', encoding='utf-8')

            w = Workflow(root, secret='super-secret-key-123', session=True, challenge='4', target_ip='10.10.10.13')
            w.execute('echo test', lambda _: 'Exit code: 0\nFLAG_EXPORT_999 super-secret-key-123')
            w.finding('FLAG_EXPORT_999', '1. Ran echo test\n2. Extracted FLAG_EXPORT_999')

            scripts_dir = w.folder / 'scripts'
            scripts_dir.mkdir(exist_ok=True)
            (scripts_dir / 'scripts_scan_1.py').write_text('print("scan")', encoding='utf-8')

            bundle_path = w.export_evidence(root / 'exported-bundle.zip')
            self.assertTrue(Path(bundle_path).is_file())

            with zipfile.ZipFile(bundle_path, 'r') as zf:
                names = set(zf.namelist())
                self.assertIn('MANIFEST.json', names)
                self.assertIn('shared-findings.md', names)
                self.assertTrue(any(n.endswith('terminal.md') for n in names))
                self.assertTrue(any(n.endswith('findings.txt') for n in names))
                self.assertTrue(any(n.endswith('scripts_scan_1.py') for n in names))
                self.assertTrue(any(n.endswith('command-ledger.jsonl') for n in names))
                # Secret config files must never be included
                self.assertFalse(any(n.endswith('.sgptrc') for n in names))
                self.assertFalse(any(n.endswith('provider-keys.json') for n in names))
                # Secret values must never appear anywhere in the archive
                for name in names:
                    raw = zf.read(name).decode('utf-8', errors='replace')
                    self.assertNotIn('super-secret-key-123', raw)
                manifest = json.loads(zf.read('MANIFEST.json').decode('utf-8'))
                self.assertEqual(manifest['shared_findings_count'], 1)

    def test_peer_sync_merges_remote_and_local_findings_bidirectionally(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            w = Workflow(root, session=True, challenge='1', target_ip='10.10.10.11')
            w.execute('ipconfig', lambda _: 'Exit code: 0\nFLAG_WIN11_LOCAL')
            w.finding('FLAG_WIN11_LOCAL', 'Found on Win11-Client')

            remote_findings = [
                {
                    'flag': 'FLAG_PARROT_REMOTE',
                    'how_found': '1. Ran nmap from Parrot\n2. Found service flag',
                    'challenge': 'challenge-2',
                    'session_id': 'challenge-2_remote',
                    'target_ip': '10.10.10.13',
                    'host': 'parrot',
                    'recorded_at': '2026-11-20T12:00:00+00:00',
                }
            ]
            pushed_payloads = []

            def fake_runner(cmd, **kwargs):
                joined = ' '.join(cmd)
                if '--export-findings-json' in joined:
                    return SimpleNamespace(returncode=0, stdout=json.dumps(remote_findings), stderr='')
                if '--import-findings-json' in joined:
                    pushed_payloads.append(json.loads(kwargs.get('input', '[]')))
                    return SimpleNamespace(returncode=0, stdout='Imported 2 findings.', stderr='')
                raise AssertionError('Unexpected SSH command: ' + joined)

            summary = w.sync_peer('attacker@10.10.10.13', runner=fake_runner)
            self.assertIn('2', summary)
            merged = w.shared_findings()
            self.assertEqual({item['flag'] for item in merged}, {'FLAG_WIN11_LOCAL', 'FLAG_PARROT_REMOTE'})
            self.assertEqual(len(pushed_payloads), 1)
            self.assertEqual({item['flag'] for item in pushed_payloads[0]}, {'FLAG_WIN11_LOCAL', 'FLAG_PARROT_REMOTE'})
            board_md = (root / 'shared-findings.md').read_text(encoding='utf-8')
            self.assertIn('FLAG_WIN11_LOCAL', board_md)
            self.assertIn('FLAG_PARROT_REMOTE', board_md)

    def test_invalid_peer_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Workflow(Path(folder), session=True)
            for bad in ('', 'attacker@10.10.10.13; rm -rf /', '-oProxyCommand=evil', 'user@host with spaces'):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    w.sync_peer(bad)


if __name__ == '__main__':
    unittest.main()
