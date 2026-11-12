# Terminal challenge comparison — 2026-11-12, Asia/Dhaka

**Recommendation: DeepSeek primary, StepFun as a manually selected alternative.**
Both completed three of four challenges. DeepSeek was faster on the completed
ones. Neither completed the reverse Windows-to-Parrot SSH fingerprint task.
This is a small operational comparison, not an exam guarantee or a general
cybersecurity benchmark ranking. The web screenshot's scores were not used.

Only Parrot attacker (`10.10.10.13`) and Server 2022 Administrator
(`10.10.10.22`) were authorized. No exploits, password attempts, configuration
changes, package installation or active probes outside those two machines ran.
All scored tool commands were requested by the actual sgpt model and passed
through its existing guard. Unknown tool commands were inspected and approved
individually; no blanket approval was introduced.

## Short-response API speed

Three interleaved trials per profile requested only `LATENCY_READY`, with high
reasoning, no tools and the same wrapper/context. All six returned that text.
Times measure complete nonstreaming API responses, including reasoning and
network time. They are not time-to-first-token or pure network RTT.

| Profile | Trial API seconds | Median | Mean |
|---|---|---:|---:|
| DeepSeek via OpenRouter | 1.067, 1.249, 0.499 | 1.067 s | 0.938 s |
| Step 5 Preview | 3.459, 1.592, 1.421 | 1.592 s | 2.157 s |

CLI startup took roughly another 1.1 seconds on Parrot. Provider caches,
generation lengths, routing and load vary; three trials are not a statistical
latency study. Reproduce from the repository using the installed exam Python:

```bash
~/.local/share/shellgpt-exam/venv/bin/python ./exam/measure_api_latency.py --repeats 3
```

## Challenges and correctness

| Challenge | DeepSeek | StepFun | DeepSeek API wait / calls | StepFun API wait / calls |
|---|---|---|---:|---:|
| Parrot: Nmap services + Server 2022 SSH fingerprint | Correct | Correct | 8.844 s / 2 | 14.138 s / 3 |
| Parrot: SMB dialects and signing requirement | Correct | Correct | 3.678 s / 2 | 5.419 s / 2 |
| Parrot: TShark HTTP request/response + encoded artifact | Correct | Correct | 8.839 s / 4 | 23.789 s / 6 |
| Server 2022: Parrot TCP22 + ED25519 fingerprint | Partial, incomplete | No usable result | 41.691 s / 8 | 32.447 s / 1 |

For the three completed challenges, API waits total **21.361 seconds versus
43.346 seconds**. Tool runtime, interactive approval delays and CLI startup
are excluded. The reverse case is reported separately rather than removed from
the correctness count. Both profiles used the existing 4,096-output-token cap
per response and eight-turn limit. Calls are not equal reasoning work or cost.

1. **Nmap and public host key.** Each model inspected only TCP
   22,80,135,139,443,445,3389 on `.22` with a TCP connect/version scan, then used
   `ssh-keyscan` and `ssh-keygen`. Both reported open ports 22,135,139,445,
   OpenSSH for Windows 9.5, and the correct ED25519 fingerprint. These matched
   native listener data and `.22`'s actual public host-key file. StepFun omitted
   the requested `--version-light` flag although its prose claimed light
   detection; both models' final data was correct. Some answers included
   preamble/Markdown despite the JSON-only instruction; formatting was scored
   separately from factual correctness.
2. **SMB configuration.** Only `smb-protocols` and `smb2-security-mode` NSE
   scripts ran against `.22:445`. Both correctly reported SMB1 not offered,
   SMB2/3 signing not required, and dialects 2.0.2,2.1,3.0,3.0.2,3.1.1.
   Independent `Get-SmbServerConfiguration` confirmed SMB1 disabled, SMB2
   enabled and `RequireSecuritySignature=false`. No vulnerability or successful
   exploitation was inferred just from those settings.
3. **Offline forensics.** A synthetic 18-packet PCAP contained a failed POST,
   a successful POST and a successful GET decoy. Both used actual TShark output
   to select stream 1, request frame 10 and response frame 11 (HTTP 200), then
   URL/Base64 decoded the correct artifact. Their answers exactly matched the
   independently generated method, path, status, addresses and random token.
   This was a generated training capture, not captured production/lab traffic.
   No token was saved as an exam finding.
4. **Reverse SSH.** DeepSeek proved TCP22 reachable, then encountered the
   actual Windows OpenSSH 9.5p2 `ssh-keyscan` error
   `choose_kex: unsupported KEX method sntrup761x25519-sha512@openssh.com`
   against Parrot OpenSSH 10.3p1. It tried unsupported `-o` / `-O` options and
   searched for another local binary before reaching the eight-turn limit.
   It did not obtain the requested fingerprint. StepFun's valid interactive
   run returned 4,096 output tokens but no visible answer or tool request.
   Neither is a full pass; the client issue was not repaired mid-test.

The first noninteractive attempts could not accept guard approval and were
stopped. They ran no approved commands and were excluded as harness failures.
The successful runs used interactive terminals. Each prompt was the same for
both profiles; first-run order alternated across challenge types, but only one
valid attempt per model/case was scored. Manual approvals make wall-clock
comparisons unsuitable, hence the separate API-wait totals.

## Reproduce the packet task

Generate a new capture and retain its printed answer separately from the model:

```text
python ./exam/make_packet_challenge.py http-evidence.pcap --client 10.10.10.13 --server 10.10.10.22
```

This sends no packets. Place the file on the analysis machine, then ask sgpt
to use TShark to identify the POST answered by HTTP 200, extract its `artifact`
form value, URL-decode and Base64-decode it. Require method, path, status, source,
destination and decoded artifact. Do not supply the generated answer to the
model, execute captured payloads, or save this fixture as an exam finding.

For live checks, explicitly authorize the target and ports. Use Nmap
`-sT -sV --version-light` on the seven listed ports, followed by an ED25519
`ssh-keyscan`/`ssh-keygen` check; use only the two named SMB scripts on TCP445.
Run each task separately with `--profile openrouter-deepseek` or
`--profile stepfun`, and approve only the exact in-scope commands. Compare
answers to the target's native configuration/public host keys, not to the other
model's answer. Terminal evidence remains under Desktop/CEH-Exam/<target-IP>.

## Changes prompted by the tests

- Named chats and caches now have separate profile directories, so switching
  between saved endpoints cannot silently reuse another model's tool metadata.
  Legacy shared chats are retained on disk but not automatically imported.
- Empty assistant responses, output-limit responses and tool-limit exhaustion
  now leave the task incomplete with a specific message. They are not reported
  as success or mislabelled solely as a billing/key problem.
- Profiles select one endpoint/key per request; saving more profiles adds no
  additional API requests. There is no automatic cross-platform failover.

## Current exam-kit validation

On the same date, the updated kit was applied without package installation to
Parrot `attacker` and Server 2022 `Administrator`. Plain `sgpt` / `sgpt-lab`
select StepFun; `sgpt-exam` selects OpenRouter DeepSeek. The four installed
runtime/configuration module hashes match the repository copies.

- Real DeepSeek function calls executed exactly `pwd` / `Get-Location`, each
  with exit code 0, and searched `find_ceh_reference` for Nmap. Both returned
  the correct working directory and a supported service-enumeration recipe;
  the example scan was not executed.
- `sgpt-exam "init the machine"` collected all three local checks successfully
  on both accounts, with a completed one-call DeepSeek review. The explicitly
  configured tools roots indexed 4,141 candidate files per account; this is a
  path catalog, not an installed-tool count or execution validation.
- New evidence is written once to `terminal.md`, with task headings and
  quoted terminal lines. Historical `terminal.txt` remains unchanged. Indexed
  output spans were independently read back, and known provider keys were
  absent from the new transcripts. Findings remain plain text.
- Windows SSH exposed a `UnicodeEncodeError` when printing a valid review.
  The runtime now configures UTF-8 stdout/stderr; a legacy-encoding regression
  test passes, and a fresh live Windows review printed successfully.
- Recipe ranking was corrected so `nmap`, `sqlmap` and `hashing` queries return
  command examples before inventory tables. References are loaded in bounded
  excerpts; no entire library is attached to every API request.

Two initial noninteractive smoke-test SSH sessions waited for stdin before an
API call; those owned processes were stopped. The final inspection-only runs
used `ssh -n` to close stdin. Commands requiring interactive guard approval
instead need an interactive terminal (`ssh -tt`); closed stdin never grants
approval. These harness attempts were not additional benchmark results.

Tool references: [Nmap version detection](https://nmap.org/book/man-version-detection.html)
and [TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html).
