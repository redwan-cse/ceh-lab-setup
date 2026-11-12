# Traffic analysis: Wireshark, TShark, Tcpdump, Yersinia

Use this page for saved lab captures. Examples are reference commands, not proof
that a tool is installed; check [Linux inventory](inventory-linux.md) and
[Windows inventory](inventory-windows.md) first.
Use copies of evidence, preserve the original SHA-256, and record the tool version.
No installation, interface configuration, or live capture is authorized by this page.
Paths such as `capture.pcapng` refer to an explicitly supplied local artifact.

## Choose a task

| Task | Tool | Platform / mode | Report evidence |
|---|---|---|---|
| Inspect a packet and conversation | Wireshark | Windows/Linux GUI | Frame, time, endpoints, relevant fields |
| Extract repeatable HTTP fields | TShark | Windows/Linux CLI | Filter, field names, extracted rows |
| Inspect numeric packet summaries | Tcpdump | Linux/Unix CLI | BPF expression, summary lines |
| Identify a layer-2 testing tool | Yersinia | Linux/Unix; high-impact functions manual | Version/help and scoped authorization |

## Wireshark — inspect a saved capture

Task → open a supplied capture and narrow the display without changing it.
Syntax → **File → Open**, then enter a display filter in the filter bar.
Example → open `capture.pcapng`, apply `http.request`, select a request and expand
**Hypertext Transfer Protocol** in Packet Details.
For a specific conversation use `ip.addr == 192.0.2.10 && tcp.port == 80`.
Use **Follow → TCP Stream** only for the selected conversation; it may show
reassembled application content that requires a smaller, redacted report excerpt.
Report → frame number, timestamp/timezone, source/destination, request method,
host and URI, plus the filter and screenshot or copied field values.
Wireshark is a GUI tool here; TShark below supplies the equivalent repeatable CLI.
Sources: [Wireshark user guide](https://www.wireshark.org/docs/wsug_html/),
[display filter reference](https://www.wireshark.org/docs/man-pages/wireshark-filter).

## TShark — HTTP fields, DNS and TCP streams offline

Task → list plaintext HTTP request metadata in a saved capture.
Syntax → `tshark -n -r FILE -Y FILTER -T fields -e FIELD ...`.
`-r` selects offline input; `-n` disables name resolution. `-Y` is a display
filter, and `-T fields` produces text. `-w` writes packets, not a text report.

```bash
tshark -n -r capture.pcapng -Y 'http.request' -T fields -E header=y -e frame.number -e frame.time_epoch -e ip.src -e ip.dst -e http.request.method -e http.host -e http.request.uri
tshark -n -r capture.pcapng -Y 'dns.flags.response == 0' -T fields -e frame.number -e dns.qry.name
tshark -n -r capture.pcapng -Y 'tcp.stream == 0' -V
```

The first command works unchanged in PowerShell when `tshark` resolves to the
verified executable; a quoted executable path needs the PowerShell `&` operator.
For IPv6 add `-e ipv6.src -e ipv6.dst`. Epoch timestamps avoid display-timezone
ambiguity. Output is tab-separated unless configured otherwise.

Task → save HTTP rows for a report in an existing output directory (PowerShell).

```powershell
tshark -n -r .\capture.pcapng -Y 'http.request' -T fields -E header=y -e frame.number -e http.request.method -e http.host -e http.request.uri | Set-Content -LiteralPath .\http-requests.tsv -Encoding UTF8
```

Report → original capture SHA-256, exact filter and fields, output path, frame
numbers and matching rows. Preserve original URI spelling; redact sensitive data
in the report copy. A blank result does not prove absence: HTTP may be encrypted,
on an undecoded port, missing from the capture, or use HTTP/2 or HTTP/3 fields.
Source: [official TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html).

## Tcpdump — offline summaries with capture-filter syntax

Task → inspect packets to/from a lab host without resolving names.
Syntax → `tcpdump -nn -r FILE 'BPF_EXPRESSION'`.

```bash
tcpdump -nn -r capture.pcap 'host 192.0.2.10 and tcp port 80'
tcpdump -nn -r capture.pcap -c 10 'udp port 53'
```

`-nn` keeps host addresses and ports numeric; `-c 10` limits displayed matching
packets. These are BPF filters, so Wireshark expressions such as `http.request`
are invalid here. Captured HTTP need not use port 80; port numbers alone do not
identify the application. Do not omit `-r`, which would change to live capture.
Native Windows Tcpdump availability is unverified; use TShark's `-r` workflow
on Windows rather than assuming WinDump has been installed.
Report → full command, input hash, timezone, matching summary lines and limits
such as truncation/snap length. Use TShark for parsed HTTP host/URI fields.
Source: [upstream Tcpdump manual source](https://github.com/the-tcpdump-group/tcpdump/blob/master/tcpdump.1.in).

## Yersinia — identify only; active layer-2 tasks are manual

Task → identify the available build and review help without a network exercise.
Syntax/example → `yersinia -V` and `yersinia -h` on the approved Linux host.
Report → tool identity/version, supported interfaces/modes described in help,
and the separate task authorization if an active exercise is later requested.
Source: [upstream parser and help](https://github.com/tomac/yersinia/blob/master/src/parser.c).

Yersinia implements layer-2 attack functions; it is not an offline pcap reader.
Interactive/GUI mode availability depends on build options. Do not launch a
default session, choose an interface, enable a daemon, or start an attack from
an automated suggestion. Such work needs explicit per-task authorization,
an isolated owned lab, manual review, and the existing command guard.
To investigate STP/DHCP evidence already captured, use Wireshark or TShark:

```bash
tshark -n -r capture.pcapng -Y 'stp' -V
```

Report → frame numbers and actual protocol fields. An observed topology message
alone does not establish that Yersinia generated it.

## Report handoff

Include capture filename/hash, tool/version, exact command or GUI filter,
matching frames, timestamp basis, concise interpretation and limitations.
Keep evidence rows separate from hypotheses. Record “no matching frames” when
appropriate rather than inventing a host, URL or recovered object.
