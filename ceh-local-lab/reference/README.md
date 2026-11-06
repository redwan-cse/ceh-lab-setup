# Historical source supplied by the user

[gemini-hyper-v-guide.md](gemini-hyper-v-guide.md) is an unchanged copy of
`J:\Downloads\Browser\ceh_practical_hyper_v_lab_setup_guide.md`, supplied on
2026-11-06. SHA256:

```text
580C949946DF945E5D8B139938F82EF81ACE8B8CB82CEB5070D30FB5E4A5E9C8
```

This is a historical Gemini-generated setup account, **not the current runbook
or proof that every described service is installed**. Start with the
[beginner guide](../BEGINNER-GUIDE.md) for current instructions.

Known differences found during the 2026-11-06 review:

- Server 2019 and Server 2022 are standalone WORKGROUP servers. AD DS, DNS,
  IIS and FTP roles are not installed; the source's role labels are plans.
  SQL has not been verified as provisioned. Do not use `10.10.10.19` as DNS
  until a functioning DNS service is actually configured and tested.
- The original OpenSSH fallback hard-codes an old MSI filename under a
  `latest/download` URL. Use the maintained `universal` kit instead.
- The original Windows examples disable every firewall profile. The existing
  lab retains that historical configuration; a new installation should keep
  its firewall enabled and allow the intended services explicitly.
- Network assignment blocks are provisioning steps, not daily repair commands.
  They can select the wrong adapter or conflict with an existing address.
- Windows 11 OOBE behavior depends on the installed version; the old bypass
  command is not a guaranteed current installation method.
- The Android Generation 1 instructions describe this particular image and
  procedure. ADB reachability must be checked. Applying a checkpoint reverts
  changes and can discard work.
- Android's expected `.9` address did not answer ARP, ping or TCP/5555 checks
  during review. Its VM state and console were not inspected, so its power
  state is unknown. The supplied Android root-console procedure was not run.
- The host gateway/NAT were found, but UAC elevation was canceled. Current VM
  switch membership and power states still require an administrator host check.
  Host AC sleep remained five hours; Parrot's five sleep/hibernate targets were
  successfully masked with the maintained local keep-awake script.
- Windows 11/Server 2022 backup DNS was corrected from `.19` to `1.1.1.1`,
  alongside `8.8.8.8`. All four SSH-accessible guests passed fresh ShellGPT
  API checks; this does not establish availability of every planned lab role.

No passwords, API keys or private keys were present in the supplied file.
