# Matched local comparison — 2026-11-12 (Asia/Dhaka)

All three profiles passed this small test. **DeepSeek through OpenRouter was
fastest in this run**; StepFun was faster than the Gemini mix. StepFun remains
the installed default, and either alternative can be selected explicitly.
These results do not establish superior results across the CEH exam or
guarantee future API availability.

See also the later [real terminal challenges and API-only timings](LAB-CHALLENGES.md),
which include Nmap, SMB, SSH interoperability and offline TShark analysis.

Both VMs used the same repository runtime, ShellGPT 1.5.1, rules, context
format, approval guard and IP-based evidence layout. StepFun ran first after
the generated-log reset. The mix used per-request overrides, leaving StepFun
as the default.
DeepSeek was tested afterward with the same cases and a per-request override.

| VM | Profile | Passed | API requests | Case time sum | Input tokens | Output tokens |
|---|---|---:|---:|---:|---:|---:|
| Parrot attacker, 10.10.10.13 | StepFun | 3/3 | 4 | 12.28 s | 3,660 | 1,109 |
| Server 2022 Administrator, 10.10.10.22 | StepFun | 3/3 | 4 | 19.84 s | 4,042 | 794 |
| Parrot attacker, 10.10.10.13 | Flash + Carbon | 3/3 | 6 | 36.90 s | 3,819 | 596 |
| Server 2022 Administrator, 10.10.10.22 | Flash + Carbon | 3/3 | 6 | 52.03 s | 4,326 | 666 |
| Parrot attacker, 10.10.10.13 | OpenRouter DeepSeek | 3/3 | 4 | 9.40 s | 3,678 | 493 |
| Server 2022 Administrator, 10.10.10.22 | OpenRouter DeepSeek | 3/3 | 4 | 16.55 s | 4,062 | 866 |

Times include CLI startup, local checks and API waits; these are sums of case
times, not wall-clock time across the parallel VM runs. Providers tokenize and
bill differently; Step Plan credits differ from Google's API billing. These
token counts alone do not establish which costs less.

OpenRouter reported $0.00035046792 for Parrot and $0.000549549 for Server 2022,
totalling **$0.00090001692** for the six DeepSeek cases (eight requests).
These are returned `usage.cost` values, not estimates from the listing's
headline rates. They do not establish the cost of future tasks or include
unreported charges. Comparable monetary usage was not returned in the earlier
Step Plan / Google runs.

1. **Initialization:** sgpt collected local settings and cached neighbors, then
   StepFun / Carbon / DeepSeek reviewed the corresponding bounded summary.
2. **Actual command:** sgpt called the guarded tool exactly once for `date` /
   `Get-Date`. The test checked actual output and exit status through indexed
   transcript evidence. In the mix, Carbon independently reviewed that output
   with no tools available.
3. **Interpretation:** given only a STALE neighbor and no authorized range,
   both drivers correctly returned `offline_proven=false` and
   `scope_authorized=false`, with no command execution. Carbon reviewed the
   mix's answer. Flash wrapped JSON in Markdown fences; the test checked the
   parsed values and Carbon noted the format deviation. StepFun returned plain JSON.
   DeepSeek also returned plain JSON with both boolean values false.

All six Carbon reviews in the mix returned visible text. Earlier Carbon-as-
executor failures remain unresolved: it was not the executor here. Reviews
used low reasoning with a 1,536-output-token cap; both drivers used high
reasoning with a 4,096-output-token cap.

The DeepSeek profile uses exactly `deepseek/deepseek-v4.1-flash-1017` through
`https://openrouter.ai/api/v1`. Reasoning/output budgets are translated to
OpenRouter's request format, compatible upstream parameters are required and
backup attempts are disabled. No cross-platform or model fallback was used.

Raw prompts, actual commands, outputs, responses, reviews and usage remain in
each VM's Desktop/CEH-Exam/<IP>/terminal.txt. No invented flags were saved and
no active subnet discovery ran. Windows and Parrot display different local
time zones; UTC task timestamps support correlation.

Reproduce using [compare_profiles.py](compare_profiles.py) and the commands in
[README.md](README.md). The cases test integration and basic evidence reasoning,
not full exam-solving capability. Rerun smoke tests before relying on a profile.
