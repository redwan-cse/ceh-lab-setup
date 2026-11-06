# Validation record

Previously verified local machines: Windows 11 (.11), Windows Server 2019
(.19), Parrot Security 7.4 (.13), and now Windows Server 2022 (.22).

The universal Windows source passed PowerShell 5.1 config/asset/service-path
fixtures. Current official OpenSSH MSI metadata and download were checked:
digest matched, Authenticode status was Valid, signer Microsoft Corporation.
That MSI was not installed on the host PC. The VM tests reused existing SSH.

The standalone launcher was copied by itself to .22 and bootstrapped missing
signed Python before installing ShellGPT. SSH setup on .22 preserved a before/
after snapshot of IPv4 addresses, prefix lengths, DNS and routes, and retained
password/public-key authentication. The latest helper includes six command
guard tests and five provider/key/environment safety tests.

The Linux kit passed seven policy tests, offline SDK/CLI checks, partial-venv
recovery, and three live StepFun tests on Parrot. Server 2019 passed six guard
tests and three live tests with the earlier preserved Windows source.

These are real tested targets, not a claim that every Windows/Linux release,
third-party firewall, proxy, domain policy or unknown lab image is verified.
No raw execution logs or credentials are committed to this repository.
