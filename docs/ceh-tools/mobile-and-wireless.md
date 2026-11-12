# Mobile and wireless: ADB, PhoneSploit, APKTool, Aircrack-ng, Hashcat

Use authorized devices, supplied APKs and owned-lab offline captures only.
These are reference examples; check [Linux inventory](inventory-linux.md) and
[Windows inventory](inventory-windows.md) for readiness. No installation,
debugging-service changes, wireless reconfiguration or live connections are
authorized by this reference. Keep the existing command guard enabled.

## Task map

| Task | Tool | Mode | Report evidence |
|---|---|---|---|
| List already attached authorized devices | ADB | Windows/Linux CLI | Serial, state, model/product |
| Identify a device-control wrapper | PhoneSploit | Fork-dependent, legacy/manual | Exact repository/build and scope |
| Decode APK resources/smali statically | APKTool | Windows/Linux CLI | Manifest and relevant decoded paths |
| Analyze an owned offline WPA/WPA2-PSK capture | Aircrack-ng | CLI, platform build dependent | Selected BSSID, handshake/status |
| Identify supported hash formats | Hashcat | Windows/Linux CLI | Candidate formats, version, provenance |

## ADB — authorized device inventory only

Task → list devices known to the local ADB server.
Syntax → `adb devices -l`; example → run it with the lab's already authorized
USB device attached and preserve its row, including `device`, `offline` or
`unauthorized` status. ADB may start its local host-side server when invoked.

```powershell
adb version
adb devices -l
```

The same commands work in Linux. `device` means connected at the ADB layer;
it does not prove the Android OS is fully booted or grant permission for arbitrary
device actions. Do not change authorization, enable TCP debugging, install apps,
pull user files or invoke a device shell as part of inventory.

Manual connection example **only after explicit authorization for that device**:
`adb connect 10.10.10.9:5555`. The address is a lab example, not a discovery target
or instruction to connect now. Confirm the configured port first; Android wireless
debugging may use pairing and dynamic ports instead of legacy port 5555.
After a separately authorized connection, use `adb devices -l` for inventory.
Report → timestamp, ADB version, connection method, selected serial/state/model,
and authorization context; redact device serials in externally shared reports.
Source: [official ADB guide: devices and connections](https://developer.android.com/tools/adb).

## PhoneSploit — legacy/fork-dependent; no intrusive automation

Task → identify the requested PhoneSploit build before using its menus.
Syntax → no universal launcher is assumed. Example → record the existing local
repository origin/version and read its README as text, without launching it.
The historical project is an ADB device-control wrapper; similarly named forks
and “PhoneSploit Pro” have different dependencies and entry points.
Source example: [historical PhoneSploit repository README](https://github.com/ByteUprise/Phonesploit/blob/master/README.md).

Device-control, shell, file extraction, credential retrieval, port forwarding,
app changes and disruptive options need explicit task-specific authorization and
manual review through the existing guard. Do not automate menu choices or scan
for exposed ADB services. For the inventory task use `adb devices -l` above.
Report → exact tool identity, supported platform, approved task and affected
device; if no task is approved, state “not launched.” Legacy Python 2 references
are compatibility information, not permission to install an obsolete runtime.

## APKTool — static APK decoding without installation

Task → decode a supplied lab APK into a new working directory.
Syntax → `apktool d INPUT.apk -o NEW_DIRECTORY`.

```bash
apktool d sample.apk -o decoded-sample
grep -n 'uses-permission' decoded-sample/AndroidManifest.xml
```

Windows PowerShell, with the verified `apktool` launcher on PATH:

```powershell
apktool d .\sample.apk -o .\decoded-sample
Select-String -LiteralPath .\decoded-sample\AndroidManifest.xml -Pattern 'uses-permission' -SimpleMatch
```

Use an unused output directory; do not add `-f`, which can delete an existing
destination. Decoding can write framework/cache data locally in addition to the
output folder. It does not install or run the APK. Smali is Dalvik disassembly,
not original Java source. Do not rebuild, sign or deploy as part of this task.
Report → input SHA-256, APKTool version, command, warnings, package name,
permission lines and relevant component/export settings with decoded file paths.
A requested permission alone does not establish malicious behavior.
Source: [official APKTool CLI parameters](https://apktool.org/docs/cli-parameters/).

## Aircrack-ng — owned offline capture analysis

Task → inspect a supplied 802.11 capture for the authorized lab network.
Use TShark first to inspect handshake frames without starting recovery:

```bash
tshark -n -r owned-lab.cap -Y 'eapol' -T fields -e frame.number -e wlan.bssid -e wlan.sa -e wlan.da
```

When offline password auditing is explicitly part of the lab task, use a small
task-provided wordlist and the capture's authorized BSSID:
syntax → `aircrack-ng -a 2 -b BSSID -w WORDLIST CAPTURE`.
Example → `aircrack-ng -a 2 -b 02:00:00:00:00:01 -w lab-candidates.txt owned-lab.cap`.
The BSSID is an example; substitute only the owned lab BSSID verified in evidence.
This is offline WPA/WPA2-PSK auditing; it is not a WPA3 or enterprise authentication
recipe. It does not require enabling monitor mode or connecting to an access point.
Report → capture/hash, selected BSSID, observed EAPOL frames, wordlist provenance,
handshake validation/error, candidates tested and outcome; redact recovered keys.
Sources: [Aircrack-ng official usage](https://www.aircrack-ng.org/doku.php?id=aircrack-ng),
[TShark field/filter options](https://www.wireshark.org/docs/man-pages/tshark.html).
No deauthentication, injection, jamming or live capture is included here.

## Hashcat — identify a supplied offline hash format

Task → list supported interpretations before selecting any recovery mode.
Syntax/example → `hashcat --identify lab.hash`; `hashcat --example-hashes` lists
the tool's supported example encodings. Windows may use `hashcat.exe` instead.
Newer/older builds vary; check `hashcat --help` rather than forcing unknown flags.
`--identify` can return several candidates; length alone cannot identify a hash.
Report → exact input provenance, Hashcat version, candidate algorithms and
the task-supplied format confirmation. Do not label candidates as confirmed.
Source: [official Hashcat options](https://hashcat.net/wiki/doku.php?id=hashcat).

Wireless pcap/cap files are not automatically Hashcat hash files. WPA formats
require the correct independently verified conversion and matching mode; no
converter installation or capture conversion is assumed here. Use the direct
Aircrack-ng offline workflow when appropriate. Any recovery run needs a specific
authorized input, mode, candidate scope and reporting destination; no live login
attempts or automatic device actions follow from an offline result.
