#Requires -Version 5.1
<#
.SYNOPSIS
Read-only host-side inventory and reachability checks for the CEH local lab.
.DESCRIPTION
Run from the Windows Hyper-V host. An elevated PowerShell session is needed for
the Hyper-V/NAT inventory. Codex sandbox approval does not grant Windows admin
rights. No guest credentials, SSH keys, or API key files are read.

An open TCP port proves a listener accepted a connection, not authentication or
application health. ICMP and TCP results are independent of VM power state.
UDP DNS and guest DNS configuration are not verified by this host-side check.
.EXAMPLE
.\Test-CehLab.ps1
.EXAMPLE
.\Test-CehLab.ps1 -SkipHyperV -OutputPath .\ceh-health.json
#>
[CmdletBinding()]
param(
    [string]$OutputPath,
    [switch]$SkipHyperV,
    [ValidateRange(100, 30000)][int]$TcpTimeoutMs = 750,
    [switch]$FunctionsOnly
)

function New-CehCheck {
    param([string]$Area, [string]$Target, [string]$Status, [string]$Detail)
    [pscustomobject][ordered]@{ Area = $Area; Target = $Target; Status = $Status; Detail = $Detail }
}

function Test-CehAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CehTcpPort {
    param([string]$Address, [int]$Port, [int]$TimeoutMs = 750)
    $client = New-Object System.Net.Sockets.TcpClient
    $waitHandle = $null
    try {
        $pending = $client.BeginConnect($Address, $Port, $null, $null)
        $waitHandle = $pending.AsyncWaitHandle
        if (-not $waitHandle.WaitOne($TimeoutMs, $false)) {
            return [pscustomobject]@{ Open = $false; Detail = 'Timed out (filtered, unreachable, or no response).' }
        }
        $client.EndConnect($pending)
        return [pscustomobject]@{ Open = $true; Detail = 'TCP connection accepted; authentication and application health untested.' }
    }
    catch {
        return [pscustomobject]@{ Open = $false; Detail = 'Connection not accepted: ' + $_.Exception.GetBaseException().Message }
    }
    finally {
        if ($null -ne $waitHandle) { $waitHandle.Close() }
        $client.Close()
    }
}

function Test-CehPing {
    param([string]$Address, [int]$TimeoutMs = 750)
    $ping = New-Object System.Net.NetworkInformation.Ping
    try { return ($ping.Send($Address, $TimeoutMs).Status -eq [System.Net.NetworkInformation.IPStatus]::Success) }
    catch { return $false }
    finally { $ping.Dispose() }
}

function Get-CehHealthReport {
    param([switch]$SkipHyperV, [int]$TcpTimeoutMs = 750)
    $checks = New-Object 'System.Collections.Generic.List[object]'
    $vmInventory = @()
    $adapterInventory = @()
    $hostAddresses = @()
    $powerInventory = @()
    $switchName = 'CEH-Lab-Switch'
    $natName = 'CEH-Lab-NAT'

    if ($SkipHyperV) {
        $checks.Add((New-CehCheck 'Hyper-V' 'Inventory' 'Unknown' 'Skipped by request. Run without -SkipHyperV in an elevated Windows PowerShell session to verify VMs, switch, NAT, and adapters.'))
    }
    elseif (-not (Test-CehAdministrator)) {
        $checks.Add((New-CehCheck 'Hyper-V' 'Inventory' 'Unknown' 'Windows administrator elevation is required. Open PowerShell as Administrator and rerun. Codex sandbox approval does not elevate Windows privileges.'))
    }
    else {
        try {
            $switch = Get-VMSwitch -Name $switchName -ErrorAction Stop
            $status = 'Fail'
            if ([string]$switch.SwitchType -eq 'Internal') { $status = 'Pass' }
            $checks.Add((New-CehCheck 'Hyper-V' $switchName $status ('Switch type: ' + $switch.SwitchType + '; expected Internal.')))
        }
        catch { $checks.Add((New-CehCheck 'Hyper-V' $switchName 'Unknown' ('Could not inspect switch: ' + $_.Exception.Message + ' Verify in elevated PowerShell.'))) }

        try {
            $nat = @(Get-NetNat -ErrorAction Stop | Where-Object { $_.Name -eq $natName })
            if ($nat.Count -eq 0) {
                $checks.Add((New-CehCheck 'NAT' $natName 'Fail' 'Expected named NAT was not found.'))
            }
            else {
                $prefixes = @($nat | ForEach-Object { [string]$_.InternalIPInterfaceAddressPrefix })
                $status = 'Fail'
                if ($prefixes -contains '10.10.10.0/24') { $status = 'Pass' }
                $checks.Add((New-CehCheck 'NAT' $natName $status ('Internal prefixes: ' + ($prefixes -join ', ') + '; expected 10.10.10.0/24.')))
            }
        }
        catch { $checks.Add((New-CehCheck 'NAT' $natName 'Unknown' ('Could not inspect NAT: ' + $_.Exception.Message + ' Verify in elevated PowerShell.'))) }

        try {
            $vms = @(Get-VM -ErrorAction Stop)
            foreach ($vm in $vms) {
                $adapters = @(Get-VMNetworkAdapter -VMName $vm.Name -ErrorAction Stop)
                foreach ($adapter in $adapters) {
                    $adapterInventory += [pscustomobject]@{
                        VMName = $vm.Name; AdapterName = $adapter.Name
                        SwitchName = $adapter.SwitchName; MacAddress = $adapter.MacAddress
                        ReportedIPAddresses = @($adapter.IPAddresses)
                    }
                }
                $onLabSwitch = @($adapters | Where-Object { $_.SwitchName -eq $switchName }).Count -gt 0
                $vmInventory += [pscustomobject]@{
                    Name = $vm.Name; State = [string]$vm.State; Status = [string]$vm.Status
                    Generation = $vm.Generation; ProcessorCount = $vm.ProcessorCount
                    MemoryAssignedBytes = $vm.MemoryAssigned; OnLabSwitch = $onLabSwitch
                }
                if ($onLabSwitch) {
                    $status = 'Warn'
                    if ([string]$vm.State -eq 'Running') { $status = 'Pass' }
                    $checks.Add((New-CehCheck 'VM power' $vm.Name $status ('Hyper-V state: ' + $vm.State + '. This does not prove guest networking or service health.')))
                }
                elseif ($vm.Name -match 'CEH|WinServer|Win11|Parrot|Android') {
                    $checks.Add((New-CehCheck 'VM adapter' $vm.Name 'Warn' ('Possible lab VM has no adapter on ' + $switchName + '; confirm intended network in Hyper-V Manager.')))
                }
            }
            if (@($vmInventory | Where-Object { $_.OnLabSwitch }).Count -eq 0) {
                $checks.Add((New-CehCheck 'Hyper-V' 'Lab VM inventory' 'Warn' ('No VMs attached to ' + $switchName + ' were found.')))
            }
        }
        catch { $checks.Add((New-CehCheck 'Hyper-V' 'VM inventory' 'Unknown' ('VM/adapter enumeration incomplete: ' + $_.Exception.Message + ' Rerun in elevated PowerShell with the Hyper-V module available.'))) }
    }

    try {
        $hostAddresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop | Select-Object InterfaceAlias, InterfaceIndex, IPAddress, PrefixLength)
        $gateway = @($hostAddresses | Where-Object { $_.IPAddress -eq '10.10.10.1' -and $_.PrefixLength -eq 24 -and $_.InterfaceAlias -eq ('vEthernet (' + $switchName + ')') })
        $status = 'Fail'
        if ($gateway.Count -gt 0) { $status = 'Pass' }
        $checks.Add((New-CehCheck 'Host IP' 'Lab gateway' $status ('Expected 10.10.10.1/24 on vEthernet (' + $switchName + '). Host address inventory is included in JSON.')))
    }
    catch { $checks.Add((New-CehCheck 'Host IP' 'Lab gateway' 'Unknown' ('Could not read host addresses: ' + $_.Exception.Message))) }

    try {
        $powerInventory = @(& powercfg.exe /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1 | ForEach-Object { [string]$_ })
        if ($LASTEXITCODE -ne 0) { throw 'powercfg query failed.' }
        # AC index appears before DC index in powercfg output; avoid localized labels.
        $indices = @($powerInventory | Where-Object { $_ -match '0x[0-9a-fA-F]+\s*$' })
        if ($indices.Count -lt 2) { throw 'Could not identify AC/DC sleep indices in powercfg output.' }
        $acMatch = [regex]::Match($indices[$indices.Count - 2], '0x([0-9a-fA-F]+)\s*$')
        $acSeconds = [Convert]::ToUInt32($acMatch.Groups[1].Value, 16)
        $status = 'Warn'
        if ($acSeconds -eq 0) { $status = 'Pass' }
        $checks.Add((New-CehCheck 'Host power' 'AC sleep timeout' $status ('Current plan AC sleep timeout: ' + $acSeconds + ' seconds (0 = Never). Other policies and lid actions are not checked.')))
    }
    catch { $checks.Add((New-CehCheck 'Host power' 'AC sleep timeout' 'Unknown' ('Could not read AC sleep policy: ' + $_.Exception.Message))) }

    $endpoints = @(
        [pscustomobject]@{ Address = '10.10.10.9'; Label = 'Android'; Ports = @(5555) },
        [pscustomobject]@{ Address = '10.10.10.11'; Label = 'Windows 11'; Ports = @(22, 445) },
        [pscustomobject]@{ Address = '10.10.10.13'; Label = 'Parrot'; Ports = @(22) },
        [pscustomobject]@{ Address = '10.10.10.19'; Label = 'Windows Server 2019'; Ports = @(22, 445) },
        [pscustomobject]@{ Address = '10.10.10.22'; Label = 'Windows Server 2022'; Ports = @(22, 445) }
    )
    foreach ($endpoint in $endpoints) {
        $target = $endpoint.Label + ' (' + $endpoint.Address + ')'
        $status = 'Warn'
        if (Test-CehPing -Address $endpoint.Address -TimeoutMs $TcpTimeoutMs) { $status = 'Pass' }
        $checks.Add((New-CehCheck 'ICMP' $target $status 'Ping is an independent reachability check; no response may mean ICMP is blocked.'))
        foreach ($port in $endpoint.Ports) {
            $tcp = Test-CehTcpPort -Address $endpoint.Address -Port $port -TimeoutMs $TcpTimeoutMs
            $status = 'Warn'
            if ($tcp.Open) { $status = 'Pass' }
            $checks.Add((New-CehCheck 'TCP' ($target + ':' + $port) $status $tcp.Detail))
        }
        $matches = @($adapterInventory | Where-Object { @($_.ReportedIPAddresses) -contains $endpoint.Address })
        if ($matches.Count -gt 0) {
            $checks.Add((New-CehCheck 'IP inventory' $endpoint.Address 'Info' ('Hyper-V integration reports this address on: ' + (($matches | ForEach-Object { $_.VMName }) -join ', ') + '. Guest labels are expected roles, not authenticated identities.')))
        }
        else {
            $checks.Add((New-CehCheck 'IP inventory' $endpoint.Address 'Unknown' 'No matching Hyper-V reported address. Integration-service IP reporting may be unavailable; endpoint identity remains unverified.'))
        }
    }
    $checks.Add((New-CehCheck 'DNS' 'Guest DNS and UDP/53' 'Unknown' 'Not tested. TCP probes do not validate UDP DNS, guest resolver configuration, or Internet access.'))
    $overall = 'Checks passed with unverified areas'
    if (@($checks | Where-Object { $_.Status -eq 'Warn' -or $_.Status -eq 'Unknown' }).Count -gt 0) { $overall = 'Attention or further verification needed' }
    if (@($checks | Where-Object { $_.Status -eq 'Fail' }).Count -gt 0) { $overall = 'Configuration mismatch found' }
    [pscustomobject][ordered]@{
        GeneratedAt = (Get-Date).ToString('o'); ComputerName = $env:COMPUTERNAME
        Overall = $overall; Checks = @($checks.ToArray()); VMs = @($vmInventory)
        VMAdapters = @($adapterInventory); HostIPv4Addresses = @($hostAddresses)
        PowerPolicyQuery = @($powerInventory)
        Scope = 'Host-side read-only checks. Planned/optional TCP ports that do not accept connections are warnings. No guest login, API key inspection, or configuration changes.'
    }
}

if (-not $FunctionsOnly) {
    $report = Get-CehHealthReport -SkipHyperV:$SkipHyperV -TcpTimeoutMs $TcpTimeoutMs
    $report.Checks | Format-Table Area, Target, Status, Detail -AutoSize -Wrap
    Write-Host $report.Overall
    if ($OutputPath) {
        $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8 -ErrorAction Stop
        Write-Host ('JSON report written to ' + $OutputPath)
    }
}
