# Parrot accounts at 10.10.10.13

| User | Purpose | Verified access |
|---|---|---|
| redwan | Original desktop/lab account | SSH, sudo, existing per-user ShellGPT |
| attacker | Additional practice account | sudo group, password SSH, host public-key SSH |

The requested attacker password was set privately and is not included in Git.
The private SSH key stays on the host; only its public key is in attacker's
authorized_keys file. Directory/file modes are 700/600 with attacker ownership.
Password authentication remains enabled. Sudo still requires authentication;
no passwordless-sudo rule was added.

From Windows host PowerShell:

```powershell
ssh attacker@10.10.10.13
```

On Parrot:

```bash
whoami
id
sudo -k
sudo id -u
```

After entering the account password, the final command should print `0`.
Password login, key-only login and password-authenticated sudo were tested.

## Reproduce the account setup

From the host, copy the helper and a public key (not a private key):

```powershell
scp .\ceh-local-lab\Create-ParrotAttacker.sh redwan@10.10.10.13:
scp "$env:USERPROFILE\.ssh\id_ed25519.pub" redwan@10.10.10.13:host-login-key.pub
ssh redwan@10.10.10.13
```

In that Parrot session:

```bash
bash ~/Create-ParrotAttacker.sh ~/host-login-key.pub
```

The helper prompts for the new password; rerunning it resets that password
interactively. It never disables password login or copies a private key.

ShellGPT is per-user. Creating attacker does not copy redwan's API key or private
configuration. To install ShellGPT for attacker later, run the Linux installer
as attacker and configure that user's protected API-key file explicitly.
