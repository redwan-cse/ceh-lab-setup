# Offline forensics, steganography and cryptography

These are reference recipes, not installation claims. Check [Linux inventory](inventory-linux.md)
and [Windows inventory](inventory-windows.md); no installation/configuration changes are authorized.
Use a copy of the supplied artifact and record its original SHA-256.
Use a fresh output folder for derived files; never execute recovered artifacts.
Linux examples use a POSIX shell. Windows equivalents appear where practical.

## File — identify format before selecting a parser

Task → identify an unknown file by content. Tool/syntax → `file FILE`.
Example → `file evidence.bin`; use `file --mime-type evidence.bin` for MIME type.
Linux/Unix CLI; Windows requires a separately verified port, not a built-in cmdlet.
Report → full description, MIME type, size, SHA-256 and format confidence.
An extension or “data” result does not establish encryption or the AES mode.
Source: [upstream file manual](https://github.com/file/file/blob/master/doc/file.man).

## 7-Zip — list an archive without extraction

Task → list names/sizes and test integrity. Syntax → `7z l ARCHIVE`, `7z t ARCHIVE`.
Example → `7z l evidence.7z`; `7z t evidence.7z` reads/decompresses for verification.
Windows PowerShell: `7z.exe l .\evidence.7z` if the verified command is on PATH.
Linux's executable may be `7zz` or `7z`; consult inventory, do not assume a path.
Report → archive type, member paths/sizes, encryption indicators and test status.
Supply a known password interactively when requested; do not place it in logs.
Sources: [official CLI help source](https://github.com/ip7z/7zip/blob/main/CPP/7zip/UI/Console/Main.cpp),
[7-Zip project](https://www.7-zip.org/).

## Strings — printable strings with offsets

Task → find embedded text without running a binary. GNU syntax:
`strings -a -n 6 -t x FILE`; example → `strings -a -n 6 -t x sample.bin`.
`-a` scans the whole file, `-n 6` sets minimum length, `-t x` prints hex offsets.
For UTF-16LE with GNU Strings use `strings -a -e l -n 6 sample.bin`.
Windows Sysinternals Strings is a different implementation; verify its help.
Report → encoding/options, offsets and relevant excerpts; strings are leads,
not proof that a URL was contacted. [GNU manual](https://sourceware.org/binutils/docs/binutils/strings.html).

## BinText — legacy Windows GUI; verify identity first

Task → review text strings in a lab binary. GUI syntax/workflow → open an
already verified BinText build, select the artifact, scan and save a text listing.
Example → inspect `sample.exe` as data; retain offsets and encoding columns.
Report → exact product/version, source provenance, input hash and saved rows.
BinText is a legacy Foundstone/McAfee name. No current authoritative manual was
verified during this review, so no CLI, download mirror or install path is assumed.
Use the documented GNU Strings workflow if this legacy tool is unavailable.

## Ghidra — local static decompilation (GUI workflow)

Task → inspect a function without executing the specimen. Workflow → create a
non-shared local project → **File → Import File** → select `sample.exe` → open
in CodeBrowser → review Auto-Analysis options → inspect the Decompiler pane.
Windows/Linux GUI workflow; Ghidra also has headless tooling, not used here.
Report → input hash, detected format/language, function address, decompiler
excerpt and analysis assumptions. Do not use debugger, emulation or specimen scripts.
Source: [official beginner guide](https://ghidra.re/ghidra_docs/GhidraClass/Beginner/Introduction_to_Ghidra_Student_Guide.html).

## Radare2 — binary metadata using its Rabin2 utility

Task → inspect headers/imports/strings without starting the sample.
Syntax/examples → `rabin2 -I sample.exe`, `rabin2 -i sample.exe`,
`rabin2 -zz sample.exe`. Cross-platform CLI when that build is available.
Report → architecture, format, imports and string offsets; record each command.
These are static reads; avoid debugger flags, write modes and external scripts.
Source: [official Radare2 book: Rabin2](https://book.rada.re/tools/rabin2/intro.html).

## Steghide — inspect supported cover files

Task → inspect a suspected carrier. Syntax/example → `steghide info cover.jpg`.
Answer **n** to the embedded-data prompt for metadata only. A later authorized
extraction with a known password uses `steghide extract -sf cover.jpg -xf recovered.bin`;
enter it interactively. Never overwrite an existing output or execute it.
Linux CLI; Windows builds require verified inventory. Report → cover format,
capacity, prompt outcome, extraction status and recovered file hash if applicable.
Source: [official Steghide manual](https://steghide.sourceforge.net/documentation/manual.pdf).

## Zsteg — inspect PNG/BMP bit planes

Task → locate possible hidden data. Syntax/example → `zsteg suspect.png`.
Linux/Ruby CLI; a Windows environment is unverified. `zsteg -a suspect.png`
tries additional supported checks and may generate many false positives.
Report → exact bit/channel/order label and offset/text preview. Confirm a
candidate with independent file identification before calling it recovered data.
Source: [upstream Zsteg usage](https://github.com/zed-0xff/zsteg#usage).

## OpenStego — extract a known compatible image (GUI workflow)

Task → recover a supplied lab payload. Workflow → **Data Hiding → Extract Data**,
select `cover.png`, choose a new output directory and supply the known password
if needed. Windows/Linux Java GUI workflow; OpenStego also has CLI support,
whose launcher/path must be verified separately before use.
Report → plugin/mode, input hash, success/error and output filename/hash.
Source: [official OpenStego data-hiding workflow](https://www.openstego.com/).

## SNOW — inspect whitespace steganography

Task → estimate capacity, then decode a known unencrypted SNOW lab sample.
Syntax/examples → `snow -S message.txt`; `snow -C message.txt recovered.txt`.
`-C` is correct only if the hidden data was compressed; omit for uncompressed data.
Legacy CLI; Linux package command may be `stegsnow`, which requires identity/help
verification. Preserve trailing tabs/spaces; editors may silently remove them.
Report → compression assumption, capacity, output length/hash and validation.
Source: [author's SNOW manual](https://darkside.com.au/snow/manual.html).

## Binwalk — signature inspection, no automatic extraction

Task → inspect embedded file signatures. Syntax/example → `binwalk firmware.bin`.
Linux CLI; versions differ (v2 Python versus v3 Rust). Read local help first.
Plain signature inspection avoids `-e`/recursive extraction and external extractors.
Report → version, decimal/hex offsets, signature descriptions and confidence;
a signature hit alone does not prove a complete embedded file is recoverable.
Source: [upstream Binwalk quick start](https://github.com/ReFirmLabs/binwalk/wiki/Quick-Start-Guide).

## VeraCrypt — identify assumptions; mount read-only only after manual approval

Task → inspect an explicitly identified lab container with its supplied password.
Random-looking bytes, file size and extension cannot reliably identify VeraCrypt.
First record hash/size and task-supplied format; then request manual approval for
the mount, password entry and mount point. Windows/Linux GUI is preferred here.
Workflow/example → select `lab-container.hc` → choose an unused drive/mount point
→ **Mount Options → Mount volume as read-only** → mount using known credentials.
Verify read-only status in the UI before listing files; dismount when done.
Windows CLI reference only: `/v FILE /l LETTER /m ro`; Linux syntax differs.
Report → approval, container hash, format assumption, read-only status, mounted
listing and dismount result. Do not put passwords, PIM or keyfile contents in reports.
Source: [official Windows mount-option reference](https://veracrypt.io/en/Command%20Line%20Usage%20for%20Windows.html).

## VeraCrypt2John — unresolved/legacy tool label

Task → identify a proposed offline container-to-recovery-format converter.
Syntax/example → no verified executable/script identity, so no command is supplied.
Record the exact installed filename, version, publisher and its own usage text
before translating this label into a command. The expected Openwall path
`run/veracrypt2john.py` was not available in the upstream tree during this review.
Report → identity/status and supported container/header mode; do not guess that a
SHA-256 digest is a password-recovery hash. [Upstream John tree](https://github.com/openwall/john/tree/bleeding-jumbo/run).

## CrypTool — CrypTool 2 Windows GUI learning workflow

Task → analyze a supplied ciphertext with the matching educational template.
Workflow/example → open CrypTool 2 → select a frequency-analysis template →
paste the lab ciphertext → run the template → inspect the frequency chart.
Report → CrypTool edition, template name, input encoding, chart and interpretation.
“CrypTool” names several products; this workflow specifically means CT2.
Source: [official CrypTool 2 overview](https://www.cryptool.org/en/ct2/).

## BCTextEncoder — Windows GUI text encryption/decryption

Task → decode a known BCTextEncoder lab message using its supplied password/key.
Workflow/example → open the verified GUI → paste the encoded lab text into the
encoded-text area → choose **Decode** → provide the authorized credential manually.
Report → product/version, message format, decode status and a redacted excerpt.
No CLI is assumed. [Jetico decoding workflow](https://www.jetico.com/file-downloads/web_help/bctextencoder/html/03_using_program/03_How_To_Use.htm).

## AES-Tool — ambiguous identity; no invented executable

Task → choose the correct decoder for a specifically identified AES lab format.
Syntax/example → identify publisher/product/version and help before any command.
Record cipher mode, key size, IV/nonce, padding, salt/KDF and ciphertext encoding
from the lab specification; “AES” alone is insufficient to decode `cipher.bin`.
Report → these parameters and tool identity, or “unresolved; no decoding attempted.”
Do not install a similarly named package or upload evidence to an online AES tool.

## Report checklist

Include input/output SHA-256, size, exact command or GUI workflow, tool/version,
relevant offsets and error messages. Separate observations from format guesses.
Use [PowerShell/hash/Base64 recipes](windows-powershell.md) for basic preprocessing.
