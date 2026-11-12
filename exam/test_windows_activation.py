"""Windows command activation without changing the test account's registry."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
import sys
import venv
from unittest.mock import MagicMock,patch
import setup_exam


class WindowsActivationTests(unittest.TestCase):
    def test_user_path_is_preserved_and_desktop_is_notified(self):
        registry=MagicMock();registry.REG_EXPAND_SZ=2
        registry.QueryValueEx.return_value=(r'%USERPROFILE%\Existing;C:\Other',2)
        directory=Path('C:/Exam/bin')
        with patch.dict('sys.modules',{'winreg':registry}),patch.dict(os.environ,{'PATH':'C:/Other;C:/Exam/bin'}), \
                patch.object(setup_exam,'notify_windows_environment',return_value=True) as notify:
            setup_exam.update_windows_paths(directory)
            self.assertEqual(os.environ['PATH'],str(directory)+';C:/Other')
        value=registry.SetValueEx.call_args.args[-1]
        self.assertEqual(value,str(directory)+r';%USERPROFILE%\Existing;C:\Other')
        notify.assert_called_once_with()

    @unittest.skipUnless(os.name=='nt','Native Windows PowerShell setup')
    def test_ready_setup_survives_native_stderr_and_activates_current_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary);kit=home/'kit';kit.mkdir()
            private=home/'CEHLab/shellgpt-exam/venv'
            venv.create(private,with_pip=False)
            site=private/'Lib/site-packages'
            for name,version in [('shell-gpt','1.5.1'),('openai','2.54.0'),('typer','0.16.0'),('click','8.1.8')]:
                metadata=site/(name.replace('-','_')+'-'+version+'.dist-info');metadata.mkdir()
                (metadata/'METADATA').write_text('Name: '+name+'\nVersion: '+version+'\n')
            for name in ('Setup-Exam.ps1','Activate-Sgpt.ps1'):
                shutil.copyfile(Path(__file__).with_name(name),kit/name)
            # A harmless stub replaces installation; no pip, registry, or API calls.
            (kit/'setup_exam.py').write_text("import os,sys\nfrom pathlib import Path\np=Path(os.environ['LOCALAPPDATA'])/'CEHLab/shellgpt-exam/bin'\np.mkdir(parents=True,exist_ok=True)\n(p/'sgpt.cmd').write_text('@echo off\\necho WRAPPER_FIXTURE_OK\\n')\nprint('Harmless pip notice',file=sys.stderr)\n")
            log=home/'setup.txt'
            code="$ErrorActionPreference='Stop'; & '"+str(kit/'Setup-Exam.ps1')+"' -NoKeyPrompt *> '"+str(log)+"'; if(-not $?){exit 1}; sgpt --version"
            shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
            environment=dict(os.environ,LOCALAPPDATA=str(home),PATH=str(Path(sys.executable).parent)+';'+os.environ['PATH'])
            result=subprocess.run([str(shell),'-NoProfile','-ExecutionPolicy','Bypass','-Command',code],capture_output=True,text=True,env=environment,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('WRAPPER_FIXTURE_OK',result.stdout)
            text=log.read_text(encoding='utf-16')
            self.assertIn('Harmless pip notice',text)
            self.assertNotIn('Required setup:',text)

    @unittest.skipUnless(os.name=='nt','Native Windows PowerShell activation')
    def test_current_powershell_and_child_cmd_resolve_new_launcher(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)/'Command Folder';directory.mkdir()
            (directory/'sgpt.cmd').write_text('@echo off\necho ACTIVATION_FIXTURE_OK\n')
            helper=Path(__file__).with_name('Activate-Sgpt.ps1').resolve()
            code='& '+"'"+str(helper)+"' -CommandDirectory '"+str(directory)+"'; if(-not $?){exit 1}; sgpt; cmd.exe /d /c sgpt"
            shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
            result=subprocess.run([str(shell),'-NoProfile','-ExecutionPolicy','Bypass','-Command',code],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout.count('ACTIVATION_FIXTURE_OK'),2)


if __name__=='__main__':unittest.main()
