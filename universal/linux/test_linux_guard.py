import tempfile
import os
import signal
import time
from pathlib import Path
import unittest
from unittest.mock import patch
import linux_command_guard as guard


class LinuxGuardTests(unittest.TestCase):
    def test_inspection(self):
        for command in ('pwd', 'ls -la /tmp', 'id', 'whoami', 'uname -a',
                        'date', "date '+%Y-%m-%d'", 'ps aux', 'df -h',
                        'ls -la /tmp | head -n 2', 'ip address show', 'ss -tuln'):
            with self.subTest(command=command):
                self.assertTrue(guard.classify(command)['automatic'])

    def test_unknown_or_dangerous_requires_approval(self):
        for command in ('rm x', 'find /tmp -delete', 'sudo apt install x',
                        'pip install x', 'bash -c pwd', 'python3 -c "print(1)"',
                        'ls; rm x', 'ls\npwd', 'ls $(rm x)', 'ls `rm x`',
                        'ls > x', 'ls && pwd', 'ls || pwd', 'cat x | bash', 'date -s now',
                        'hostname newname', 'ss -K', 'ip link delete x',
                        'sort -o x y', 'uniq x y', 'ls -la &', 'ls "unterminated',
                        'env ls', './ls', '/tmp/ls', 'systemctl stop ssh',
                        'cat <(rm x)', 'ls $HOME', 'ls |', '| ls'):
            with self.subTest(command=command):
                self.assertFalse(guard.classify(command)['automatic'])

    def test_auto_exec_without_prompt(self):
        with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
            self.assertIn('Exit code: 0', guard.execute_command('pwd'))

    def test_pipeline(self):
        with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
            result = guard.execute_command('uname -s | head -n 1')
        self.assertIn('Linux', result)
        self.assertIn('Exit code: 0', result)

    def test_refusal_and_eof(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'must-not-exist'
            command = 'touch ' + str(path)
            for response in ('no', '', EOFError(), KeyboardInterrupt()):
                opts = {'side_effect': response} if isinstance(response, BaseException) else {'return_value': response}
                with patch('builtins.input', **opts):
                    self.assertIn('not executed', guard.execute_command(command))
                self.assertFalse(path.exists())

    def test_explicit_approval(self):
        with patch('builtins.input', return_value='yes'):
            result = guard.execute_command("value=approved-test; printf '%s' \"$value\"")
        self.assertIn('approved-test', result)
        self.assertIn('Exit code: 0', result)

    def test_ai_approval_handles_screenshot_readonly_chains_without_prompt(self):
        import shlex
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'fixture.txt').write_text('SYNTHETIC_DATA\n')
            commands=[
                'ls -la '+shlex.quote(directory)+' 2>/dev/null; echo HOME; ls -la '+shlex.quote(directory)+' 2>/dev/null',
                'find '+shlex.quote(directory)+" -maxdepth 2 -type f -printf '%y %p\\n' 2>/dev/null | head -50",
                'grep -rIl SYNTHETIC '+shlex.quote(directory)+' 2>/dev/null | head -20; file '+shlex.quote(str(path/'fixture.txt'))+'; head -c 600 '+shlex.quote(str(path/'fixture.txt')),
            ]
            with patch('builtins.input',side_effect=AssertionError('Human prompt is not expected')):
                for command in commands:
                    approved=[]
                    result=guard.execute_command(command,auto_approve=lambda value:approved.append(value) or True)
                    self.assertIn('Exit code: 0',result)
                    self.assertEqual(approved,[command])

    def test_ai_deferral_still_needs_human_approval(self):
        with patch('builtins.input',return_value='no'):
            self.assertIn('not executed',guard.execute_command('unknown_command',auto_approve=lambda _:False))

    def test_ai_approved_shell_does_not_source_hidden_startup_code(self):
        import shlex
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/'unexpected'
            startup=Path(directory)/'startup.sh'
            startup.write_text('touch '+shlex.quote(str(marker)))
            with patch.dict(os.environ,{'BASH_ENV':str(startup)}),patch('builtins.input',side_effect=AssertionError('Unexpected prompt')):
                result=guard.execute_command("printf SYNTHETIC_ENV_OK",auto_approve=lambda _:True)
            self.assertIn('SYNTHETIC_ENV_OK',result)
            self.assertFalse(marker.exists())

    def test_timeout_kills_background_child_after_shell_exits(self):
        import shlex
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory) / 'child-pid'
            script = 'sleep 30 & echo $! > ' + shlex.quote(str(pidfile))
            child = None
            try:
                with patch.object(guard.time, 'monotonic', side_effect=[0, 299.8]):
                    result = guard.run_pipeline([['/bin/bash', '-c', script]])
                self.assertIn('timed out', result)
                child = int(pidfile.read_text())
                state = Path(f'/proc/{child}/stat')
                deadline = time.monotonic() + 1
                while state.exists() and state.read_text().split(')')[1].split()[0] != 'Z' and time.monotonic() < deadline:
                    time.sleep(0.01)
                alive = state.exists() and state.read_text().split(')')[1].split()[0] != 'Z'
                self.assertFalse(alive, 'Background child survived timeout cleanup')
            finally:
                if child is None and pidfile.exists():
                    child = int(pidfile.read_text())
                if child:
                    try:
                        os.kill(child, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == '__main__':
    unittest.main()
