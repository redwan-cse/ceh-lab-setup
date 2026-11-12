"""Offline compatibility checks; no apt, downloads or package installation."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).parent
BASH=str(Path('C:/Program Files/Git/bin/bash.exe')) if Path('C:/Program Files/Git/bin/bash.exe').exists() else shutil.which('bash')


@unittest.skipUnless(BASH,'Bash unavailable')
class LinuxSetupTests(unittest.TestCase):
    def shell(self,body):
        script=(ROOT/'setup-exam.sh').resolve().as_posix()
        return subprocess.run([BASH,'-c','source "'+script+'"\n'+body],capture_output=True,text=True,timeout=15)

    def test_old_python_is_not_selected_even_with_ensurepip(self):
        result=self.shell('python3(){ return 1; }; export -f python3; candidate=""; compatible_python python3 && candidate=python3; [[ -z "$candidate" ]]')
        self.assertEqual(result.returncode,0,result.stderr)

    def test_usable_python_is_reused(self):
        result=self.shell('working_python(){ return 0; }; compatible_python working_python')
        self.assertEqual(result.returncode,0,result.stderr)

    def test_python_checks_include_version_and_venv_requirements(self):
        result=self.shell('probe(){ printf "%s\\n" "$*"; }; compatible_python probe')
        self.assertEqual(result.returncode,0,result.stderr)
        # Probe output is intentionally discarded; inspect what was requested via a file.
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'probe.txt';native=path.as_posix()
            if os.name=='nt':native='/'+native[0].lower()+native[2:]
            result=self.shell('probe(){ printf "%s\\n" "$*" > "'+native+'"; }; compatible_python probe')
            self.assertEqual(result.returncode,0,result.stderr)
            text=path.read_text()
            self.assertIn('(3,10)',text)
            self.assertIn('ensurepip',text)
            self.assertIn('ssl',text)

    def test_python_apt_packages_are_not_requested(self):
        source=(ROOT/'setup-exam.sh').read_text()
        self.assertNotIn('packages+=(python3)',source)
        self.assertNotIn('packages+=(python3-venv)',source)
        self.assertIn('bootstrap-python-linux.sh',source)

    def test_noninteractive_missing_prerequisites_change_nothing(self):
        result=self.shell('id(){ echo 1000; }; select_python(){ return 1; }; setup_exam_main --no-key-prompt')
        self.assertEqual(result.returncode,3,result.stdout+result.stderr)
        self.assertIn('Interactive approval required',result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
