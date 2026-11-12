"""Provider switching must preserve the active configuration on failure."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import setup_exam


class SwitchModelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.root=self.home/'install';self.root.mkdir()
        (self.root/'exam_runtime.py').write_text('"""ShellGPT exam entry point; owned test installation."""\n')
        self.config=self.home/'config';self.config.mkdir()
        self.active=self.config/'.sgptrc'
        self.active.write_text('EXAM_PROFILE=stepfun\nAPI_BASE_URL=https://api.stepfun.ai/step_plan/v1\nDEFAULT_MODEL=step-5-preview\nOPENAI_API_KEY=step-dummy\nCUSTOM_SETTING=keep-me\n')
        self.keys=self.config/'provider-keys.json'
        self.keys.write_text(json.dumps({'stepfun':'step-dummy','openrouter':'router-dummy'}))
        for name,value in (('ROOT',self.root),('CONFIG',self.config)):
            p=patch.object(setup_exam,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(setup_exam,'windows_acl');p.start();self.addCleanup(p.stop)

    def run_switch(self,*arguments):
        stream=io.StringIO()
        with patch('sys.argv',['setup_exam.py','--switch-provider',*arguments]),contextlib.redirect_stdout(stream):
            setup_exam.main()
        return stream.getvalue()

    def test_switch_uses_provider_vault_and_preserves_settings(self):
        output=self.run_switch('--provider','openrouter-deepseek','--no-key-prompt')
        values=setup_exam.read()
        self.assertEqual(values['API_BASE_URL'],'https://openrouter.ai/api/v1')
        self.assertEqual(values['DEFAULT_MODEL'],'deepseek/deepseek-v4.1-flash-1017')
        self.assertEqual(values['OPENAI_API_KEY'],'router-dummy')
        self.assertNotIn('REASONING_EFFORT',values)
        self.assertEqual(values['CUSTOM_SETTING'],'keep-me')
        self.assertNotIn('router-dummy',output)
        self.assertIn('deepseek/deepseek-v4.1-flash-1017',output)
        self.run_switch('--provider','stepfun','--no-key-prompt')
        self.assertEqual(setup_exam.read()['OPENAI_API_KEY'],'step-dummy')

    def test_missing_or_declined_key_retains_active_config(self):
        self.keys.write_text(json.dumps({'stepfun':'step-dummy'}))
        before=self.active.read_bytes()
        with self.assertRaisesRegex(RuntimeError,'key'):
            self.run_switch('--provider','openrouter-deepseek','--no-key-prompt')
        self.assertEqual(self.active.read_bytes(),before)
        with patch('getpass.getpass',return_value=''):
            with self.assertRaisesRegex(RuntimeError,'key'):
                self.run_switch('--provider','openrouter-deepseek')
        self.assertEqual(self.active.read_bytes(),before)

    def test_missing_key_is_prompted_and_saved_only_for_its_provider(self):
        self.keys.write_text(json.dumps({'stepfun':'step-dummy'}))
        with patch('getpass.getpass',return_value='new-router-dummy'):
            self.run_switch('--provider','openrouter-deepseek')
        self.assertEqual(setup_exam.read()['OPENAI_API_KEY'],'new-router-dummy')
        self.assertEqual(json.loads(self.keys.read_text()),{'stepfun':'step-dummy','openrouter':'new-router-dummy'})

    def test_unowned_install_is_rejected_before_config_mutation(self):
        (self.root/'exam_runtime.py').write_text('print("unrelated")\n')
        before=self.active.read_bytes();keys=self.keys.read_bytes()
        with self.assertRaisesRegex(RuntimeError,'installation'):
            self.run_switch('--provider','openrouter-deepseek','--no-key-prompt')
        self.assertEqual(self.active.read_bytes(),before)
        self.assertEqual(self.keys.read_bytes(),keys)

    def test_failed_atomic_replace_retains_original_config(self):
        before=self.active.read_bytes()
        with patch('setup_exam.os.replace',side_effect=OSError('fixture denied')):
            with self.assertRaises(OSError):
                self.run_switch('--provider','openrouter-deepseek','--no-key-prompt')
        self.assertEqual(self.active.read_bytes(),before)

    def wrapper_dir(self):
        return self.root/'bin' if os.name=='nt' else self.home/'.local/bin'

    def test_removes_only_owned_legacy_wrappers(self):
        bindir=self.wrapper_dir();bindir.mkdir(parents=True)
        suffix='.cmd' if os.name=='nt' else ''
        for name in ('sgpt-exam','sgpt-lab'):
            (bindir/(name+suffix)).write_text(str(self.root/'exam_runtime.py'))
        with patch.object(setup_exam.Path,'home',return_value=self.home):
            setup_exam.write_wrappers('stepfun')
        self.assertEqual([p.name for p in bindir.iterdir()],['sgpt'+suffix])

    def test_unrelated_legacy_aliases_are_never_overwritten_or_removed(self):
        bindir=self.wrapper_dir();bindir.mkdir(parents=True)
        suffix='.cmd' if os.name=='nt' else ''
        for name in ('sgpt-exam','sgpt-lab'):
            target=bindir/(name+suffix);target.write_text('unrelated program')
            with patch.object(setup_exam.Path,'home',return_value=self.home):
                setup_exam.write_wrappers('stepfun',True)
            self.assertEqual(target.read_text(),'unrelated program')
            target.unlink()

    @unittest.skipUnless(os.name=='nt','Windows native switcher')
    def test_native_powershell_switcher_selects_current_user_install(self):
        installed=self.home/'CEHLab/shellgpt-exam';installed.mkdir(parents=True)
        (installed/'setup_exam.py').write_text('import json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        environment=dict(os.environ,LOCALAPPDATA=str(self.home))
        script=Path(__file__).with_name('Switch-Model.ps1')
        for name,wanted in (('deepseek','openrouter-deepseek'),('stepfun','stepfun')):
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),name],
                                  env=environment,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout),['--switch-provider','--provider',wanted])

    @unittest.skipUnless(os.name=='nt','Windows native switcher')
    def test_native_powershell_switcher_prefers_private_python(self):
        installed=self.home/'CEHLab/shellgpt-exam';installed.mkdir(parents=True)
        venv.create(installed/'venv',with_pip=False)
        (installed/'setup_exam.py').write_text('import sys\nprint(sys.prefix)\n')
        environment=dict(os.environ,LOCALAPPDATA=str(self.home))
        result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                               str(Path(__file__).with_name('Switch-Model.ps1')),'stepfun'],
                              env=environment,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(),(installed/'venv').resolve())

    def test_native_bash_switcher_selects_installed_helper_and_private_python(self):
        bash=shutil.which('bash') if os.name!='nt' else 'C:/Program Files/Git/bin/bash.exe'
        if not bash or not Path(bash).is_file():self.skipTest('Bash unavailable')
        installed=self.home/'.local/share/shellgpt-exam';installed.mkdir(parents=True)
        (installed/'setup_exam.py').write_text('import json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        private=installed/'venv/bin/python';private.parent.mkdir(parents=True)
        # A controlled executable forwards to the real Python without creating packages.
        import shlex
        private.write_text('#!/usr/bin/env bash\nexec '+shlex.quote(Path(sys.executable).as_posix())+' "$@"\n',newline='\n')
        private.chmod(0o700)
        environment=dict(os.environ,HOME=self.home.as_posix())
        for name,wanted in (('deepseek','openrouter-deepseek'),('stepfun','stepfun')):
            result=subprocess.run([bash,'--noprofile','--norc',Path(__file__).with_name('switch-model.sh').as_posix(),name],
                                  env=environment,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout),['--switch-provider','--provider',wanted])


if __name__=='__main__':unittest.main()
