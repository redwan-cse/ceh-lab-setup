<#
Run on physical Redwan-PC in Administrator PowerShell.
Default: inspect only. -RestoreAdbCheckpoint first saves a new checkpoint,
then restores the existing known ADB checkpoint on Android-8.1-Target only.
Restoration rewinds the guest disk and memory; the new backup preserves the
current state for rollback. No other VM or network adapter is changed.
#>
[CmdletBinding()]
param([switch]$RestoreAdbCheckpoint,[string]$OutputPath)
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ine 'Redwan-PC'){throw 'Run this local-lab helper on physical Redwan-PC.'}
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run Windows PowerShell as Administrator.'}
$vmName='Android-8.1-Target'
$vm=Get-VM -Name $vmName
if($vm.Generation -ne 1){throw 'Unexpected Android VM generation; inspect manually.'}
$candidates=@(Get-VMSnapshot -VMName $vmName | Where-Object {$_.Name -like 'Android-8.1-Target - adb -*'})
if($candidates.Count -ne 1){throw 'Expected exactly one existing Android ADB checkpoint; inspect manually.'}
$adbCheckpoint=$candidates[0]
Write-Host "Android state: $($vm.State); ADB checkpoint: $($adbCheckpoint.Name)"
if(-not $RestoreAdbCheckpoint){
    Write-Host 'Inspection only. To rewind this VM after approval, pass -RestoreAdbCheckpoint.'
    return
}
$backupName='before-adb-recovery-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$backup=Checkpoint-VM -Name $vmName -SnapshotName $backupName -Passthru -Confirm:$false
if(-not $backup){throw 'Current-state backup was not created; restore aborted.'}
Write-Host "Current Android state saved as: $backupName"
Restore-VMSnapshot -VMSnapshot $adbCheckpoint -Confirm:$false
$vm=Get-VM -Name $vmName
if($vm.State -eq 'Off' -or $vm.State -eq 'Saved'){Start-VM -Name $vmName | Out-Null}
$open=$false
for($attempt=0;$attempt -lt 20;$attempt++){
    $client=New-Object Net.Sockets.TcpClient
    try{
        $pending=$client.BeginConnect('10.10.10.9',5555,$null,$null)
        if($pending.AsyncWaitHandle.WaitOne(500) -and $client.Connected){$open=$true;break}
    }catch{}finally{$client.Dispose()}
    Start-Sleep -Seconds 2
}
$result=[ordered]@{
    CollectedAt=(Get-Date).ToString('o'); VM=$vmName
    BackupCheckpoint=$backupName; RestoredCheckpoint=$adbCheckpoint.Name
    VMState=(Get-VM -Name $vmName).State.ToString(); AdbTcp5555Reachable=$open
}
$json=$result|ConvertTo-Json
if($OutputPath){[IO.File]::WriteAllText([IO.Path]::GetFullPath($OutputPath),$json,(New-Object Text.UTF8Encoding($false)))}
$json
if(-not $open){Write-Warning 'Checkpoint restored but ADB still unreachable. Inspect the Android local console; do not repeat restores blindly.'}
