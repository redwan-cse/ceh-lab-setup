# Passive local inventory only: no probes, installs, or configuration writes.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Host', 'Addresses', 'Routes', 'Neighbors', 'Capabilities')]
    [string]$Section
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)

try {
    switch ($Section) {
        'Host' {
            $hostName = [Environment]::MachineName
            $account = [Environment]::UserName
            try { $account = [Security.Principal.WindowsIdentity]::GetCurrent().Name } catch {}
            $osName = [Environment]::OSVersion.VersionString
            $osInfo = $null
            try {
                $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
                if ($osInfo.Caption) { $osName = $osInfo.Caption }
            } catch {
                # Basic identity is available even if CIM is disabled or denied.
            }
            if (-not $hostName) { throw 'Cannot read the local host name' }
            Write-Output ('HostName : {0}' -f $hostName)
            Write-Output ('OS : {0}' -f $osName)
            Write-Output ('Account : {0}' -f $account)
            if ($null -ne $osInfo) {
                Write-Output ('Version : {0}' -f $osInfo.Version)
                Write-Output ('BuildNumber : {0}' -f $osInfo.BuildNumber)
                Write-Output ('LastBootUpTime : {0}' -f $osInfo.LastBootUpTime)
            }
        }
        'Addresses' {
            $addresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop)
            if ($addresses.Count -eq 0) { Write-Output 'No IPv4 addresses configured.' }
            foreach ($address in $addresses) {
                Write-Output ('InterfaceAlias : {0}' -f $address.InterfaceAlias)
                Write-Output ('InterfaceIndex : {0}' -f $address.InterfaceIndex)
                Write-Output ('IPv4Address : {0}' -f $address.IPAddress)
                Write-Output ('PrefixLength : {0}' -f $address.PrefixLength)
                Write-Output ('AddressState : {0}' -f $address.AddressState)
                Write-Output ''
            }
        }
        'Routes' {
            Write-Output 'IPv4 routes:'
            $routes = @(Get-NetRoute -AddressFamily IPv4 -ErrorAction Stop)
            if ($routes.Count -eq 0) { Write-Output 'No IPv4 routes configured.' }
            foreach ($route in $routes) {
                Write-Output ('{0} via {1} InterfaceIndex {2} metric {3}' -f $route.DestinationPrefix, $route.NextHop, $route.InterfaceIndex, $route.RouteMetric)
            }
            Write-Output ''
            Write-Output 'DNS server configuration:'
            $dns = @(Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction Stop)
            $dnsFound = $false
            foreach ($entry in $dns) {
                if (@($entry.ServerAddresses).Count -gt 0) {
                    Write-Output ('InterfaceAlias : {0}; InterfaceIndex : {1}; DNS : {2}' -f $entry.InterfaceAlias, $entry.InterfaceIndex, ($entry.ServerAddresses -join ', '))
                    $dnsFound = $true
                }
            }
            if (-not $dnsFound) { Write-Output 'No IPv4 DNS servers configured.' }
        }
        'Neighbors' {
            Write-Output 'Cached IPv4 neighbors (no discovery packets sent):'
            $neighbors = @(Get-NetNeighbor -AddressFamily IPv4 -ErrorAction Stop)
            if ($neighbors.Count -eq 0) { Write-Output 'No cached IPv4 neighbors.' }
            foreach ($neighbor in $neighbors) {
                Write-Output ('{0} MAC {1} InterfaceIndex {2} State {3}' -f $neighbor.IPAddress, $neighbor.LinkLayerAddress, $neighbor.InterfaceIndex, $neighbor.State)
            }
        }
        'Capabilities' {
            Write-Output 'Core tool availability (commands are not executed):'
            foreach ($tool in @('Get-CimInstance', 'Get-NetIPAddress', 'Get-NetRoute', 'Get-DnsClientServerAddress', 'Get-NetNeighbor', 'ipconfig.exe', 'netsh.exe', 'route.exe', 'arp.exe', 'ping.exe', 'tracert.exe', 'nslookup.exe', 'curl.exe', 'python.exe', 'python3.exe', 'py.exe', 'sgpt', 'nmap.exe', 'tshark.exe', 'openssl.exe', 'ssh.exe', 'powershell.exe', 'pwsh.exe')) {
                $command = Get-Command -Name $tool -CommandType Application, Cmdlet, Function -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($null -ne $command) {
                    Write-Output ('{0} : available ({1})' -f $tool, $command.Source)
                } else {
                    Write-Output ('{0} : missing' -f $tool)
                }
            }
        }
    }
} catch {
    [Console]::Error.WriteLine(('Host collection failed ({0}): {1}' -f $Section, $_.Exception.Message))
    exit 1
}
exit 0
