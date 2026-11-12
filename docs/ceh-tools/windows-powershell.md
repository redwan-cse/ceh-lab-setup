# PowerShell, OpenSSH, hashes, Base64, Grep, Find, Awk, Sed

Use these local recipes on supplied lab files. See [Windows inventory](inventory-windows.md)
and [Linux inventory](inventory-linux.md) for tool readiness; a command example
does not establish installation. No install/configuration changes are authorized.
Examples use relative artifact paths under the current working directory.
PowerShell is case-insensitive for cmdlet names; Linux executable names are
normally case-sensitive. GNU command examples below use a Linux/POSIX shell.

## PowerShell — inspect files and available commands

Task → locate a supplied evidence file and identify a tool's executable.
Syntax → `Get-Item -LiteralPath PATH`; `Get-Command NAME`.

```powershell
Get-Item -LiteralPath .\evidence.bin | Select-Object FullName,Length,LastWriteTimeUtc
Get-Command tshark -ErrorAction SilentlyContinue | Select-Object Name,CommandType,Source
$PSVersionTable.PSVersion
```

Report → resolved path, byte length, UTC timestamp, shell version and exact tool
identity. A missing command needs a documented installation decision, not an
automatic download. For a verified executable path containing spaces use
`& 'C:\Verified Tool Folder\tool.exe' --help`; that path is illustrative only.
Source: [Get-Item](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-item),
[Get-Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/get-command).

## OpenSSH — inspect local capabilities without a connection

Task → identify the SSH client and supported ciphers.
Syntax/examples → `ssh -V`, `ssh -Q cipher` (Windows and Linux CLI).
`ssh -V` commonly writes version output to stderr; capture both streams if needed.
Report → client/version and relevant capability lines. This does not establish
server reachability, server policy or authorization to log in.
Connection syntax reference: `ssh user@host`; supply a real host only for a
separately authorized connection. Do not disable host-key verification, inspect
private keys, or change SSH services/configuration to satisfy this local task.
Source: [official OpenSSH manual](https://man.openbsd.org/ssh).

## SHA1SUM / SHA224SUM / SHA256SUM — file integrity

Task → compute a digest before analysis. GNU syntax → `sha256sum FILE`.

```bash
sha1sum evidence.bin
sha224sum evidence.bin
sha256sum evidence.bin
sha256sum --check evidence.sha256
```

The check file must be a trusted task-supplied manifest in the expected digest
and filename format. Record the check exit status and any mismatching filenames.
SHA-1 is included for compatibility with lab questions; use SHA-256 for evidence
integrity. A digest is not encryption and cannot be “decoded.”
Source: [GNU Coreutils checksum documentation](https://www.gnu.org/software/coreutils/manual/coreutils.html).

Windows PowerShell equivalents (also available in PowerShell 7 on Linux):

```powershell
Get-FileHash -LiteralPath .\evidence.bin -Algorithm SHA1
Get-FileHash -LiteralPath .\evidence.bin -Algorithm SHA256
```

`Get-FileHash` has no built-in SHA224 algorithm. If SHA-224 is required, use an
already verified `sha224sum` implementation or record it as unavailable; do not
substitute SHA-256 or invent a `Get-FileHash -Algorithm SHA224` option.
Report → algorithm, full digest, exact path, size, comparison source and result.
Source: [Microsoft Get-FileHash supported algorithms](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash).

## Base64 — decode bytes without execution

Task → inspect a known Base64 text sample. GNU syntax → `base64 --decode FILE`.
Example → `printf '%s' 'SGVsbG8=' | base64 --decode` displays `Hello`.
For a task-provided file, `base64 --decode encoded.txt > decoded.bin` writes a
derived artifact; use a fresh filename and do not execute it.
Source: [GNU Base64 invocation](https://www.gnu.org/software/coreutils/manual/html_node/base64-invocation.html).

PowerShell equivalent for the known UTF-8 sample:

```powershell
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('SGVsbG8='))
```

For binary content preserve the bytes rather than decoding them as UTF-8:

```powershell
$decodedBytes = [Convert]::FromBase64String((Get-Content -LiteralPath .\encoded.txt -Raw))
[IO.File]::WriteAllBytes((Join-Path $PWD 'decoded.bin'), $decodedBytes)
Get-FileHash -LiteralPath .\decoded.bin -Algorithm SHA256
```

Ensure `decoded.bin` does not already exist before writing. Base64 is encoding,
not encryption. Never pass decoded text to `Invoke-Expression`, a shell, or an
interpreter. Report → input/output hashes, byte count, encoding and decode errors.
Source: [Microsoft Convert.FromBase64String](https://learn.microsoft.com/en-us/dotnet/api/system.convert.frombase64string).

## Grep — literal text with line numbers

Task → locate a URL/domain string in a supplied text listing.
GNU syntax/example → `grep -nF -- 'example.test' strings.txt`.
PowerShell → `Select-String -LiteralPath .\strings.txt -Pattern 'example.test' -SimpleMatch`.
`-F`/`-SimpleMatch` treats the period literally; default pattern matching is regex.
Report → source file hash, matching line numbers, excerpts and exact pattern.
Sources: [GNU Grep](https://www.gnu.org/s/grep/manual/grep.html),
[Select-String](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/select-string).

## Find — enumerate files under a scoped directory

Task → find only pcap files in an evidence working copy.
GNU syntax/example → `find ./evidence -type f -name '*.pcap'`.
PowerShell → `Get-ChildItem -LiteralPath .\evidence -File -Recurse -Filter '*.pcap'`.
Windows `find.exe` searches text and is not GNU Find. These examples list files;
do not add `-delete`, `-exec` or recursive actions on discovered files.
Report → search root, filename filter, full matching paths and enumeration errors.
Sources: [GNU Find manual](https://www.gnu.org/software/findutils/manual/html_mono/find.html),
[Get-ChildItem](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-childitem).

## Awk — extract whitespace-delimited columns

Task → reduce a simple lab table to endpoint and status columns.
GNU syntax/example → `awk '{print $1, $3}' endpoints.txt`.
PowerShell equivalent for a simple nonempty whitespace-delimited table:

```powershell
Get-Content -LiteralPath .\endpoints.txt | Where-Object { $_.Trim() } | ForEach-Object { $cols = $_.Trim() -split '\s+'; $cols[0],$cols[2] -join ' ' }
```

Assume at least three columns per nonempty row. This is not CSV parsing;
use `Import-Csv` for quoted CSV. Report → delimiter assumption, selected columns,
input line count and extracted rows. [GNU Awk guide](https://www.gnu.org/s/gawk/manual/gawk.html).

## Sed — select a line range without changing the source

Task → display lines 1–20 of a local text artifact.
GNU syntax/example → `sed -n '1,20p' findings.txt`.
PowerShell → `Get-Content -LiteralPath .\findings.txt -TotalCount 20`.
For preview-only substitution: `sed 's/example.test/redacted/g' findings.txt`
prints a transformed copy; it uses a regex (`.` matches any character).
For a literal domain use `sed 's/example\.test/redacted/g' findings.txt`.
Do not add `-i`, which changes the source. Report → line range or transformation,
source hash and output excerpt. [GNU Sed manual](https://www.gnu.org/software/sed/manual/sed.html).

## Evidence handling across shells

Record the shell and tool version with the command. PowerShell pipelines carry
objects; GNU pipelines generally carry text/bytes. PowerShell versions differ in
native redirection behavior, so use the byte-preserving Base64 method above for
binary output. Save a redacted report copy while retaining the original evidence.
