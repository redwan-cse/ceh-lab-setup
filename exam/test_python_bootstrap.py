"""Offline checks for the private Linux Python bootstrap (no network or installs)."""
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
BASH = (str(Path('C:/Program Files/Git/bin/bash.exe'))
        if Path('C:/Program Files/Git/bin/bash.exe').is_file() else shutil.which('bash'))


def shell_path(path):
    value = Path(path).as_posix()
    return '/' + value[0].lower() + value[2:] if os.name == 'nt' else value


@unittest.skipUnless(BASH, 'Bash unavailable')
class PrivatePythonBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.bootstrap = ROOT / 'bootstrap-python-linux.sh'
        self.env = dict(os.environ, HOME=shell_path(self.home),
                        PATH=shell_path(self.bin) + ':/usr/bin:/bin',
                        BOOTSTRAP_TEST_BIN=shell_path(self.bin),
                        BOOTSTRAP_TEST_LOG=shell_path(self.base / 'calls'),
                        UV_PYTHON_INSTALL_MIRROR='https://invalid.invalid/python',
                        UV_INSECURE_HOST='*')
        self.command('uname', 'case "$1" in -s) echo Linux;; -m) echo x86_64;; esac\n')

    def command(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/bash\n' + body, encoding='utf-8', newline='\n')
        path.chmod(0o755)

    def run_helper(self, *args):
        # Git Bash prepends its own uname/curl on startup; set the test PATH after it.
        return subprocess.run([BASH, '--noprofile', '--norc', '-c',
                               'export PATH="$BOOTSTRAP_TEST_BIN:/usr/bin:/bin"; exec /bin/bash "$@"',
                               'bootstrap-test', shell_path(self.bootstrap), *args], env=self.env,
                              capture_output=True, text=True, timeout=20)

    def fixture(self, corrupt=False, invalid_python=False):
        # Replace ONLY the trusted archive digest in a temporary copy, so a synthetic
        # release can exercise verification/extraction without fetching executable code.
        uv = '''#!/bin/bash
set -e
[[ -z ${UV_PYTHON_INSTALL_MIRROR-} && -z ${UV_INSECURE_HOST-} ]] || exit 81
printf '%s\\n' "$*" >> "$BOOTSTRAP_TEST_LOG"
if [[ "$*" == '--version' ]]; then echo 'uv 0.13.7'; exit; fi
if [[ "$*" == *'python install'* ]]; then
  [[ "$*" == *'--no-bin'* && "$*" == *'--install-dir '* ]] || exit 82
  mkdir -p "$UV_PYTHON_INSTALL_DIR/cpython-3.12-test/bin"
  printf '#!/bin/bash\\n%s\\n' '[[ "$1" == "-I" && "$2" == "-c" ]] || exit 83' 'exit PYTHON_RESULT' > "$UV_PYTHON_INSTALL_DIR/cpython-3.12-test/bin/python3.12"
  chmod +x "$UV_PYTHON_INSTALL_DIR/cpython-3.12-test/bin/python3.12"
  echo 'install noise'
elif [[ "$*" == *'python find'* ]]; then
  [[ "$*" == *'--managed-python'* && "$*" == *'--no-python-downloads'* ]] || exit 84
  [[ -f "$UV_PYTHON_INSTALL_DIR/cpython-3.12-test/bin/python3.12" ]] || exit 1
  echo "$UV_PYTHON_INSTALL_DIR/cpython-3.12-test/bin/python3.12"
else exit 85; fi
'''.replace('PYTHON_RESULT', '1' if invalid_python else '0')
        archive = self.base / 'release.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            info = tarfile.TarInfo('uv-x86_64-unknown-linux-musl/uv')
            data = uv.encode()
            info.size, info.mode = len(data), 0o755
            tar.addfile(info, io.BytesIO(data))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        content = self.bootstrap.read_text(encoding='utf-8')
        content = content.replace('287491da03f2a785c70fa75b13e1f849918c2f2b5415fe84876b8214eeb792f9', digest)
        self.bootstrap = self.base / 'helper.sh'
        self.bootstrap.write_text(content, encoding='utf-8', newline='\n')
        self.env['BOOTSTRAP_TEST_ARCHIVE'] = shell_path(archive)
        self.command('curl', '''printf 'download\\n' >> "$BOOTSTRAP_TEST_LOG"
[[ "$1" == '--disable' && "$*" == *"--proto =https"* && "$*" == *"--proto-redir =https"* ]] || exit 87
[[ "${@: -1}" == https://github.com/astral-sh/uv/releases/download/0.13.7/uv-*-unknown-linux-musl.tar.gz ]] || exit 88
while [[ $# -gt 0 ]]; do
  if [[ "$1" == '--output' ]]; then shift; cp "$BOOTSTRAP_TEST_ARCHIVE" "$1"; exit; fi
  shift
done
exit 86
''')
        if corrupt:
            archive.write_bytes(b'invalid download')

    def test_approval_required_before_any_write(self):
        for args in ((), ('--invalid',), ('--approved', 'extra')):
            result = self.run_helper(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
            self.assertEqual(list(self.home.iterdir()), [])

    def test_unsupported_platform_before_any_write(self):
        self.command('uname', 'case "$1" in -s) echo Linux;; -m) echo riscv64;; esac\n')
        result = self.run_helper('--approved')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unsupported Linux architecture', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_read_only_find_without_installation_does_not_write(self):
        result = self.run_helper('--find')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('No validated private Python', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_private_install_has_clean_stdout_and_reuses_verified_cache(self):
        self.fixture()
        for _ in range(2):
            result = self.run_helper('--approved')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), shell_path(self.home) +
                             '/.local/share/shellgpt-python/python/cpython-3.12-test/bin/python3.12')
        calls = (self.base / 'calls').read_text()
        self.assertEqual(calls.count('download\n'), 1)
        self.assertEqual(calls.count('python install'), 1)
        self.assertFalse(list((self.home / '.local/share/shellgpt-python').glob('.bootstrap.*')))
        before = {p: p.stat().st_mtime_ns for p in self.home.rglob('*')}
        result = self.run_helper('--find')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in self.home.rglob('*')})

    def test_edited_cached_uv_is_replaced_without_executing_it(self):
        self.fixture()
        self.assertEqual(self.run_helper('--approved').returncode, 0)
        private = self.home / '.local/share/shellgpt-python'
        uv = private / 'tools/uv/0.13.7/uv'
        uv.write_text('#!/bin/bash\necho tampered >> "$BOOTSTRAP_TEST_LOG"\nexit 99\n',
                      encoding='utf-8', newline='\n')
        (private / 'python/cpython-3.12-test/bin/python3.12').unlink()
        result = self.run_helper('--approved')
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.base / 'calls').read_text()
        self.assertNotIn('tampered', calls)
        self.assertEqual(calls.count('download\n'), 1)

    def test_symlink_private_root_is_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.home / '.local/share').mkdir(parents=True)
        try:
            (self.home / '.local/share/shellgpt-python').symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f'Symlink creation unavailable: {exc}')
        result = self.run_helper('--approved')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlink', result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_bad_checksum_never_executes_and_cleans_staging(self):
        self.fixture(corrupt=True)
        result = self.run_helper('--approved')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('checksum', result.stderr.lower())
        self.assertEqual((self.base / 'calls').read_text(), 'download\n')
        self.assertFalse(list((self.home / '.local/share/shellgpt-python').glob('.bootstrap.*')))

    def test_python_without_required_modules_is_rejected(self):
        self.fixture(invalid_python=True)
        result = self.run_helper('--approved')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('validation', result.stderr.lower())


if __name__ == '__main__':
    unittest.main()
