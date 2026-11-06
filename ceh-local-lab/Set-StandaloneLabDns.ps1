<# Local workgroup lab only. Never use this to configure AD DNS clients. #>
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$computer=Get-CimInstance Win32_ComputerSystem
if($computer.PartOfDomain -or $computer.DomainRole -ge 4){throw 'Domain member/DC detected: configure DNS for that domain instead.'}
if((Get-Service -Name DNS -ErrorAction SilentlyContinue).Status -eq 'Running'){throw 'A DNS server is active here; review DNS design before changing the client.'}
$addresses=@(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -in @('10.10.10.11','10.10.10.19','10.10.10.22')})
if($addresses.Count -ne 1){throw 'Expected exactly one known local-lab interface; no changes made.'}
$interface=$addresses[0]
Set-DnsClientServerAddress -InterfaceIndex $interface.InterfaceIndex -ServerAddresses @('8.8.8.8','1.1.1.1')
Get-DnsClientServerAddress -InterfaceIndex $interface.InterfaceIndex -AddressFamily IPv4 | Select-Object InterfaceAlias,ServerAddresses | Format-Table -AutoSize
Resolve-DnsName api.stepfun.ai -Type A -ErrorAction Stop | Where-Object {$_.IPAddress} | Select-Object Name,IPAddress | Format-Table -AutoSize
