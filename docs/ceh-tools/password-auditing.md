# Password auditing tasks

Use synthetic lab hashes or a hash file explicitly supplied for the exercise.
Keep hashes, candidates, recovered values, potfiles and restore/session files
outside version control. These examples were documented, not executed during
the inventory. Use the existing ShellGPT guard and its approval prompts for
tool execution. See [Parrot availability](inventory-linux.md).

## Identify the format before attempting an offline wordlist

```bash
hashcat --identify './lab-hashes.txt'
/usr/sbin/john --list=formats
```

A string's length alone does not establish its algorithm: a 32-character hex
value can represent several formats. Start with the exercise's source-system
description, compare the full serialized form with
[Hashcat's example hashes](https://hashcat.net/wiki/doku.php?id=example_hashes),
and use `--identify` as a list of possible modes. Verify John format names using
its local list. Identifying a candidate format does not verify that a password
is recoverable. [Hashcat options](https://hashcat.net/wiki/doku.php?id=hashcat)
and [John FAQ](https://www.openwall.com/john/doc/FAQ.shtml).

## Run one finite local wordlist

Replace `JOHN_FORMAT` and `HASHCAT_MODE` with the verified format and numeric
mode. Use a small, finite, exercise-specific `small-lab-candidates.txt` file.
These tools work locally on the supplied hash file and create local results.

```bash
/usr/sbin/john --format=JOHN_FORMAT --wordlist='./small-lab-candidates.txt' --session=ceh-demo --pot='./ceh-demo.john.pot' './lab-hashes.txt'
/usr/sbin/john --show --format=JOHN_FORMAT --pot='./ceh-demo.john.pot' './lab-hashes.txt'
hashcat -m HASHCAT_MODE -a 0 './lab-hashes.txt' './small-lab-candidates.txt' --runtime=60 --session=ceh-demo --potfile-path='./ceh-demo.hashcat.pot'
hashcat -m HASHCAT_MODE --show --potfile-path='./ceh-demo.hashcat.pot' './lab-hashes.txt'
```

John is installed at `/usr/sbin/john`, outside `attacker`'s audited PATH; use
that full path without changing the account PATH. Its SIMD-selected binary was
not launched by the audit. Hashcat is on PATH, but compute devices/drivers were
not tested. If its backend is unavailable, record the limitation and use the
already installed John where the format is supported. A completed wordlist
with no result means no candidate matched; it does not prove password strength.
[John examples](https://www.openwall.com/john/doc/EXAMPLES.shtml) and
[Hashcat options](https://hashcat.net/wiki/doku.php?id=hashcat).

## Bounded online check for one disposable account

Only use this when the exercise specifically authorizes online password
testing and the account's lockout policy permits it. Prepare a file containing
at most **three** approved candidates, one per line; verify it before running.
Replace `LAB_ACCOUNT` and `TARGET`. Stop if the account locks or the service
degrades.

```bash
wc -l './candidates-max3.txt'
hydra -l LAB_ACCOUNT -P './candidates-max3.txt' -t 1 -W 3 -w 5 -f 'ssh://TARGET'
```

This targets one account on one host with one connection at a time, a delay
between connections, and stop-on-success. Do not expand it to user lists or
subnets. Unlike offline auditing, this creates real authentication failures
and can lock the lab account. Never use a production account or the account
you depend on for lab access. [Hydra's own option definitions](https://github.com/vanhauser-thc/thc-hydra/blob/master/hydra.c).

## L0phtCrack on Windows

The library contains `lc7setup_v7.2.0_Win64.exe`; an installer on the share is
not proof of installation. The official project identifies 7.2.0 as its Win64
release. Use the [Windows inventory](inventory-windows.md) to determine whether
an existing copy is ready. If already installed, open its GUI manually, import
only the exercise-supplied test hashes, choose a short dictionary audit, and
review the result locally. Leave remote hash collection and scheduled jobs
unconfigured. No installer or GUI was launched by this audit.
[Official L0phtCrack release information](https://l0phtcrack.gitlab.io/).
