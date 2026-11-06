<# Local CEH VM maintenance only. Saves original scanning preferences for Restore.
Disables active scanning, not the Defender platform/service. Windows/policy can
reenable protection; use Status to verify before a lab session. Does not bypass
Tamper Protection, touch the physical host, or reboot a VM.
#>
[CmdletBinding()]
param(
    [ValidateSet('Status','Disable','Restore')][string]$Mode='Status',
    [ValidateSet('10.10.10.11','10.10.10.19','10.10.10.22')][string[]]$ComputerName=@('10.10.10.11','10.10.10.19','10.10.10.22'),
    [switch]$Local
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
if(-not $Local){
    $failed=@()
    foreach($computer in $ComputerName){
        $user=if($computer -eq '10.10.10.11'){'Win11-Client'}else{'Administrator'}
        & scp -o BatchMode=yes -o ConnectTimeout=10 $PSCommandPath "${user}@${computer}:Set-LabDefender.ps1"
        if($LASTEXITCODE -ne 0){$failed+=$computer;continue}
        & ssh -o BatchMode=yes -o ConnectTimeout=10 "$user@$computer" "powershell -NoProfile -ExecutionPolicy Bypass -File Set-LabDefender.ps1 -Local -Mode $Mode"
        if($LASTEXITCODE -ne 0){$failed+=$computer}
    }
    if($failed){throw "Action did not complete on: $($failed -join ', '). Inspect the reported reason."}
    return
}
if($env:COMPUTERNAME -notin @('DESKTOP-5AJ4QBL','WIN-4D48AGEM0CH','WIN-L4HLUP8AT8K')){throw 'This helper is restricted to the three known CEH Windows VMs.'}
function Show-DefenderState {
    $state=Get-MpComputerStatus
    $preferences=Get-MpPreference
    [ordered]@{Computer=$env:COMPUTERNAME;RealTime=$state.RealTimeProtectionEnabled;
        Behavior=$state.BehaviorMonitorEnabled;IOAV=$state.IoavProtectionEnabled;
        ScriptScanningDisabled=$preferences.DisableScriptScanning;
        AntivirusInstalledAndEnabled=$state.AntivirusEnabled;TamperProtected=$state.IsTamperProtected}|ConvertTo-Json -Compress
}
if($Mode -eq 'Status'){Show-DefenderState;return}
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as Administrator in the guest.'}
if((Get-MpComputerStatus).IsTamperProtected){Show-DefenderState;throw 'Turn Tamper Protection off through Windows Security in this VM, then rerun. No protected-setting bypass is attempted.'}
$folder=Join-Path $env:LOCALAPPDATA 'CEHLab'
$snapshot=Join-Path $folder 'defender-before.json'
if((Test-Path $folder) -and ((Get-Item $folder).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Redirected settings directory refused.'}
if((Test-Path $snapshot) -and ((Get-Item $snapshot).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Redirected settings snapshot refused.'}
$names=@('DisableRealtimeMonitoring','DisableBehaviorMonitoring','DisableIOAVProtection','DisableScriptScanning')
if($Mode -eq 'Disable'){
    if(-not (Test-Path $snapshot)){
        $p=Get-MpPreference
        $saved=[ordered]@{Computer=$env:COMPUTERNAME}
        foreach($name in $names){$saved[$name]=[bool]$p.$name}
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        $saved|ConvertTo-Json|Set-Content -LiteralPath $snapshot -Encoding UTF8
    }
    $settings=@{}
    foreach($name in $names){$settings[$name]=$true}
}else{
    if(-not (Test-Path $snapshot)){throw 'No original-state snapshot exists for this account.'}
    $saved=Get-Content -LiteralPath $snapshot -Raw|ConvertFrom-Json
    if($saved.Computer -ne $env:COMPUTERNAME){throw 'Settings snapshot belongs to another VM.'}
    $settings=@{}
    foreach($name in $names){$settings[$name]=[bool]$saved.$name}
}
Set-MpPreference @settings
for($attempt=0;$attempt -lt 12;$attempt++){
    $p=Get-MpPreference
    $match=$true
    foreach($name in $names){if([bool]$p.$name -ne [bool]$settings[$name]){$match=$false}}
    $state=Get-MpComputerStatus
    if([bool]$state.RealTimeProtectionEnabled -ne (-not [bool]$settings.DisableRealtimeMonitoring)){$match=$false}
    if([bool]$state.BehaviorMonitorEnabled -ne (-not [bool]$settings.DisableBehaviorMonitoring)){$match=$false}
    if([bool]$state.IoavProtectionEnabled -ne (-not [bool]$settings.DisableIOAVProtection)){$match=$false}
    if($match){break}
    Start-Sleep -Seconds 1
}
Show-DefenderState
if(-not $match){throw 'Requested scanning state did not take effect; inspect protection policy.'}
Write-Host "$Mode verified. Original preferences: $snapshot"
