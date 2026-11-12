"""Offline behavior checks for the passive native host collectors."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
BASH = (str(Path('C:/Program Files/Git/bin/bash.exe'))
        if Path('C:/Program Files/Git/bin/bash.exe').is_file() else shutil.which('bash'))
POWERSHELL = shutil.which('powershell') if os.name == 'nt' else None


@unittest.skipUnless(BASH, 'Bash unavailable')
class ParrotCollectorTests(unittest.TestCase):
    def run_section(self, section, ip_body=None):
        with tempfile.TemporaryDirectory() as folder:
            if ip_body is not None:
                helper = Path(folder) / 'ip'
                helper.write_text('#!/bin/bash\n' + ip_body, encoding='utf-8')
                helper.chmod(0o755)
            helper_path = Path(folder).as_posix()
            if os.name == 'nt':
                helper_path = '/' + helper_path[0].lower() + helper_path[2:]
            env = dict(os.environ, PATH=helper_path)
            return subprocess.run([BASH, (ROOT / 'collect-host-parrot.sh').as_posix(), '--section', section],
                                  text=True, capture_output=True, env=env, timeout=15)

    def test_addresses_returns_interface_evidence_without_other_ip_operations(self):
        result = self.run_section('addresses', '[[ "$*" == "-brief address" ]] || exit 91\n'
                                  'echo "eth0 UP 10.20.30.40/24"\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('10.20.30.40/24', result.stdout)

    def test_routes_preserves_default_gateway_on_one_line(self):
        result = self.run_section('routes', '[[ "$*" == "-4 route show" ]] || exit 91\n'
                                  'echo "default via 10.20.30.1 dev eth0"\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('default via 10.20.30.1 dev eth0', result.stdout.splitlines())

    def test_missing_required_ip_and_failed_query_are_failures(self):
        for body in (None, 'exit 7\n'):
            result = self.run_section('addresses', body)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('ip', result.stderr.lower())

    def test_empty_neighbor_cache_is_success(self):
        result = self.run_section('neighbors', '[[ "$*" == "-4 neighbor show" ]] || exit 91\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No cached', result.stdout)

    def test_missing_optional_tools_is_success_and_invalid_section_is_rejected(self):
        result = self.run_section('capabilities')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r'ip\s*:\s*missing')
        self.assertNotEqual(self.run_section('scan').returncode, 0)


@unittest.skipUnless(POWERSHELL, 'Windows PowerShell unavailable')
class WindowsCollectorTests(unittest.TestCase):
    def run_section(self, section, fixture=''):
        script = str(ROOT / 'collect-host-windows.ps1').replace("'", "''")
        return subprocess.run([POWERSHELL, '-NoProfile', '-NonInteractive', '-Command',
                               fixture + f"\n& '{script}' -Section '{section}'"],
                              text=True, capture_output=True, timeout=30)

    def test_addresses_exposes_ipv4_as_workflow_evidence(self):
        result = self.run_section('Addresses', """
function Get-NetIPAddress { [pscustomobject]@{IPAddress='10.20.30.40';InterfaceAlias='Ethernet';InterfaceIndex=3;PrefixLength=24;AddressState='Preferred'} }
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r'IPv4Address\s*:\s*10\.20\.30\.40')
        self.assertIn('Ethernet', result.stdout)

    def test_routes_keeps_gateway_in_default_row_and_includes_dns(self):
        result = self.run_section('Routes', """
function Get-NetRoute { [pscustomobject]@{DestinationPrefix='0.0.0.0/0';NextHop='10.20.30.1';InterfaceIndex=3;RouteMetric=25} }
function Get-DnsClientServerAddress { [pscustomobject]@{InterfaceAlias='Ethernet';InterfaceIndex=3;ServerAddresses=@('10.20.30.2')} }
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r'0\.0\.0\.0/0[^\r\n]*10\.20\.30\.1')
        self.assertIn('10.20.30.2', result.stdout)

    def test_empty_neighbors_is_success_and_failed_query_is_failure(self):
        empty = self.run_section('Neighbors', 'function Get-NetNeighbor {}')
        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertIn('No cached', empty.stdout)
        failed = self.run_section('Neighbors', "function Get-NetNeighbor { throw 'fixture access denied' }")
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn('fixture access denied', failed.stderr)

    def test_host_falls_back_without_cim_and_optional_tools_can_be_missing(self):
        host = self.run_section('Host', "function Get-CimInstance { throw 'CIM unavailable' }")
        self.assertEqual(host.returncode, 0, host.stderr)
        self.assertIn('HostName', host.stdout)
        self.assertIn('Account', host.stdout)
        self.assertIn('OS', host.stdout)
        caps = self.run_section('Capabilities', 'function Get-Command {}')
        self.assertEqual(caps.returncode, 0, caps.stderr)
        self.assertRegex(caps.stdout, r'ipconfig(?:\.exe)?\s*:\s*missing')


if __name__ == '__main__':
    unittest.main()
