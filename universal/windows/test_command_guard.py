import tempfile
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import shellgpt_command_guard as guard


class PolicyTests(unittest.TestCase):
    def test_literal_inspection_runs_automatically(self):
        for command in (
            'Get-Location', 'Get-ChildItem -LiteralPath "C:\\Windows"',
            'Get-Process | Select-Object -First 2 -Property Name,Id',
            'Get-Date', 'Get-Service -Name "Spooler"',
            'Microsoft.PowerShell.Management\\Get-Location',
            "Get-Content input.txt | Select-String -Pattern '[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$' | Sort-Object -Unique",
            'Get-Location; Get-Date',
            'Get-FileHash -LiteralPath input.txt -Algorithm SHA256',
            'Resolve-DnsName -Name example.com -Type MX',
        ):
            with self.subTest(command=command):
                decision = guard.classify(command)
                self.assertTrue(decision['automatic'], decision)
                self.assertIn('DnsClient\\' if command.startswith('Resolve-DnsName') else 'Microsoft.PowerShell.', decision['command'])

    def test_risky_unknown_and_obfuscated_commands_require_approval(self):
        for command in (
            'Remove-Item x', 'del x', 'rm x', 'rmdir x',
            'winget install Example', 'pip install requests', 'python -m pip install x',
            'Install-Module Example', 'msiexec /i x.msi', 'choco upgrade all',
            'python -c "print(1)"', '.\\example.ps1', 'cmd /c dir',
            'Get-Date; Remove-Item x', 'Get-Date\nGet-Location',
            'Get-Content $(Remove-Item x)', 'Get-Content "$([IO.File]::Delete(\'x\'))"',
            'Get-Process | ForEach-Object { Remove-Item x }',
            '& Get-Date', '. Get-Date', 'Get-Date > x',
            'Get-Date -OutVariable x', 'Get-Date -ErrorVariable x',
            'Get-Date # comment', 'gci', 'Get-Location -UnexpectedParam x',
            'Get-ChildItem -Path $env:TEMP', 'Get-ChildItem -Path (Get-Location)',
            'Get-Date && Get-Location', 'Get-Date | Set-Content x',
            'Get-Process -Name "unterminated', 'FakeModule\\Get-Location',
        ):
            with self.subTest(command=command):
                self.assertFalse(guard.classify(command)['automatic'])

    def test_automatic_execution_returns_output(self):
        with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
            result = guard.execute_command('Get-Location')
        self.assertIn('Exit code: 0', result)

    def test_denial_and_missing_input_do_not_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'should-not-exist'
            command = "[IO.File]::WriteAllText('" + str(path).replace("'", "''") + "','x')"
            for answer in ('n', '', EOFError(), KeyboardInterrupt()):
                with self.subTest(answer=repr(answer)):
                    options = {'side_effect': answer} if isinstance(answer, BaseException) else {'return_value': answer}
                    with patch('builtins.input', **options):
                        result = guard.execute_command(command)
                    self.assertIn('not executed', result)
                    self.assertFalse(path.exists())

    def test_explicit_approval_runs_exact_command(self):
        with patch('builtins.input', return_value='yes'):
            result = guard.execute_command("$value = 'approved-test'; Write-Output $value")
        self.assertIn('approved-test', result)
        self.assertIn('Exit code: 0', result)

    def test_classifier_failure_refuses_execution(self):
        with patch.object(guard, 'classify', side_effect=RuntimeError('classifier failed')):
            self.assertIn('not executed', guard.execute_command('Get-Date'))

    def test_routine_download_and_report_outputs_stay_in_exam_folder(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'CEH_EXAM_DIR':folder}):
            path=str(Path(folder)/'report.txt')
            for command in ("Invoke-WebRequest -UseBasicParsing -Uri 'https://example.com' -OutFile '"+path+"'",
                            "Get-Content input.txt | Out-File -Encoding utf8 -FilePath '"+path+"'"):
                self.assertTrue(guard.classify(command)['automatic'])
            for command in ("Invoke-WebRequest -Uri 'https://example.com' -Method POST",
                            "Get-Date | Out-File -FilePath 'C:\\outside.txt'",
                            "Get-Content input.txt | Out-File -FilePath '"+str(Path(folder)/'terminal.md')+"'"):
                self.assertFalse(guard.classify(command)['automatic'])
            Path(path).write_text('preserve')
            self.assertFalse(guard.classify("Get-Date | Out-File -FilePath '"+path+"'")['automatic'])
            self.assertFalse(guard.classify("Get-Date | Out-File -Append:0 -FilePath '"+path+"'")['automatic'])
            self.assertFalse(guard.classify("Invoke-WebRequest -UseBasicParsing:0 -Uri 'https://example.com'")['automatic'])

    def test_routine_report_executes_without_prompt(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'CEH_EXAM_DIR':folder}):
            source=Path(folder)/'input.txt';source.write_text('contact training@example.test\n')
            output=Path(folder)/'report.txt'
            command="Get-Content -LiteralPath '"+str(source)+"' | Select-String -Pattern 'training@.*' | Out-File -Encoding utf8 -FilePath '"+str(output)+"'"
            with patch('builtins.input',side_effect=AssertionError('Unexpected approval prompt')):
                result=guard.execute_command(command)
            self.assertIn('Exit code: 0',result)
            self.assertIn('training@example.test',output.read_text(encoding='utf-8-sig'))

    def test_broken_output_link_requires_approval(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'CEH_EXAM_DIR':folder}):
            path=Path(folder)/'report.txt'
            try:path.symlink_to(Path(folder)/'missing.txt')
            except OSError:self.skipTest('Symlink privileges unavailable')
            self.assertFalse(guard.classify("Get-Date | Out-File -FilePath '"+str(path)+"'")['automatic'])


if __name__ == '__main__':
    unittest.main()
