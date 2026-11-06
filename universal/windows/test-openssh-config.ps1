$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'setup-openssh-windows-universal.ps1'
if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'FAIL: universal SSH script is missing' }
. $scriptPath -FunctionsOnly
function Assert-True($Condition, $Message) { if (-not $Condition) { throw "FAIL: $Message" } }
$source = "# header`r`nPort 2222`r`nPasswordAuthentication no`r`nPubkeyAuthentication no`r`nMaxAuthTries 6`r`nMatch Group administrators`r`n    AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys`r`n    PasswordAuthentication no`r`n"
$result = Get-LabSshConfigText -Text $source -Port 22
Assert-True ($result.StartsWith("Port 22`r`nPasswordAuthentication yes`r`nPubkeyAuthentication yes`r`n")) 'global settings precede Match'
Assert-True ($result.Contains('MaxAuthTries 6')) 'default preserves existing auth limits'
Assert-True ($result.Contains("    PasswordAuthentication no")) 'Match block remains untouched'
Assert-True ($result -eq (Get-LabSshConfigText -Text $result -Port 22)) 'config generation is idempotent'
$tuned = Get-LabSshConfigText -Text $source -Port 2200 -EnableLabAuthTuning
Assert-True ($tuned.Contains("MaxAuthTries 20`r`nMaxStartups 50:30:100")) 'lab tuning is explicit'
Assert-True (-not $tuned.Contains('MaxAuthTries 6')) 'old global auth limit is replaced when opted in'
$release = [pscustomobject]@{ assets = @(
    [pscustomobject]@{ name = 'OpenSSH-Win32-v10.4.0.0.msi'; browser_download_url = 'https://github.com/PowerShell/Win32-OpenSSH/releases/download/v1/x86.msi'; digest = ('sha256:' + ('a' * 64)) },
    [pscustomobject]@{ name = 'OpenSSH-Win64-v10.4.0.0.msi'; browser_download_url = 'https://github.com/PowerShell/Win32-OpenSSH/releases/download/v1/x64.msi'; digest = ('sha256:' + ('b' * 64)) }
) }
$asset = Select-LabSshReleaseAsset -Release $release -Architecture AMD64
Assert-True ($asset.name -eq 'OpenSSH-Win64-v10.4.0.0.msi') 'release selects native architecture'
Assert-True ((Select-LabSshReleaseAsset -Release $release -Architecture x86).name -like 'OpenSSH-Win32-*') '32 bit release selects Win32'
$rejected = $false
try { Select-LabSshReleaseAsset -Release $release -Architecture ARM64 | Out-Null } catch { $rejected = $true }
Assert-True $rejected 'missing native architecture fails rather than silently installing x64'
$exe = Get-LabSshServiceExecutable -PathName '"C:\Program Files\OpenSSH\sshd.exe" -D'
Assert-True ($exe -eq 'C:\Program Files\OpenSSH\sshd.exe') 'quoted MSI service path resolves'
Assert-True ((Get-LabSshServiceExecutable -PathName 'C:\Windows\System32\OpenSSH\sshd.exe') -eq 'C:\Windows\System32\OpenSSH\sshd.exe') 'capability service path resolves'
$raw = Get-Content -LiteralPath $scriptPath -Raw
Assert-True ($raw -notmatch '(?i)\b(New-NetIPAddress|Set-NetIPAddress|Set-DnsClientServerAddress|Set-NetIPInterface|Disable-NetAdapter|Enable-NetAdapter|Remove-NetIPAddress|New-NetRoute)\b') 'script never mutates network addressing'
$tokens = $null; $errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$errors)
Assert-True ($errors.Count -eq 0) 'PowerShell parser accepts script'
Write-Host 'PASS: universal OpenSSH configuration, asset selection, service paths, and network invariants'
