<# Run elevated. Read-only unless -KeepAwakeOnAC is explicitly selected. #>
[CmdletBinding()]
param([string]$OutputPath, [switch]$KeepAwakeOnAC)
$ErrorActionPreference='Stop'
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
    throw 'Open Windows PowerShell as Administrator to inspect Hyper-V.'
}
$state=[ordered]@{
    CollectedAt=(Get-Date).ToString('o')
    ComputerName=$env:COMPUTERNAME
    VMs=@(Get-VM | Select-Object Name,@{n='State';e={$_.State.ToString()}},Status,Generation,ProcessorCount,MemoryAssigned,MemoryStartup,@{n='AutomaticStartAction';e={$_.AutomaticStartAction.ToString()}},@{n='AutomaticStopAction';e={$_.AutomaticStopAction.ToString()}},@{n='Uptime';e={$_.Uptime.ToString()}})
    Switches=@(Get-VMSwitch | Select-Object Name,@{n='SwitchType';e={$_.SwitchType.ToString()}},NetAdapterInterfaceDescription)
    Adapters=@(Get-VMNetworkAdapter -All | Select-Object VMName,Name,SwitchName,Status,IPAddresses)
    Checkpoints=@(Get-VM | Get-VMSnapshot | Select-Object VMName,Name,CreationTime,@{n='SnapshotType';e={$_.SnapshotType.ToString()}})
    NAT=@(Get-NetNat | Select-Object Name,InternalIPInterfaceAddressPrefix,Active)
    Addresses=@(Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,PrefixLength)
    Memory=(Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory)
    SleepBefore=@(& powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE)
    HibernateBefore=@(& powercfg /query SCHEME_CURRENT SUB_SLEEP HIBERNATEIDLE)
    PowerChanged=$false
}
if($KeepAwakeOnAC){
    & powercfg /change standby-timeout-ac 0
    if($LASTEXITCODE -ne 0){throw 'Could not disable automatic host sleep on AC.'}
    & powercfg /change hibernate-timeout-ac 0
    if($LASTEXITCODE -ne 0){throw 'Could not disable automatic host hibernation on AC.'}
    $state.PowerChanged=$true
}
$state.SleepAfter=@(& powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE)
$state.HibernateAfter=@(& powercfg /query SCHEME_CURRENT SUB_SLEEP HIBERNATEIDLE)
$json=$state | ConvertTo-Json -Depth 7
if($OutputPath){[IO.File]::WriteAllText([IO.Path]::GetFullPath($OutputPath),$json,(New-Object Text.UTF8Encoding($false)))}
$json
