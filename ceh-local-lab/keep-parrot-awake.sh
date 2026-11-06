#!/usr/bin/env bash
# Persistent guest sleep prevention. Run on Parrot as the normal lab user.
# Does not change networking, shut down sessions, or suspend/reboot the VM.
set -euo pipefail
targets=(sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target)
if [[ "${1:-}" == '--check' ]]; then
    for target in "${targets[@]}"; do
        state="$(systemctl is-enabled "$target" 2>/dev/null || true)"
        printf '%s: %s\n' "$target" "$state"
        [[ "$state" == masked ]] || exit 1
    done
    echo 'PASS: all guest sleep/hibernate targets are persistently masked.'
    exit 0
fi
if [[ "$(id -u)" == 0 ]]; then admin=(); else sudo -v; admin=(sudo); fi
temporary="$(mktemp -d)"
trap 'rm -f -- "$temporary/logind.conf" "$temporary/sleep.conf"; rmdir -- "$temporary"' EXIT
cat > "$temporary/logind.conf" <<'EOF'
[Login]
IdleAction=ignore
HandleSuspendKey=ignore
HandleHibernateKey=ignore
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
EOF
cat > "$temporary/sleep.conf" <<'EOF'
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowHybridSleep=no
AllowSuspendThenHibernate=no
EOF
"${admin[@]}" install -d -m 755 /etc/systemd/logind.conf.d /etc/systemd/sleep.conf.d
"${admin[@]}" install -m 644 "$temporary/logind.conf" /etc/systemd/logind.conf.d/80-ceh-lab-no-sleep.conf
"${admin[@]}" install -m 644 "$temporary/sleep.conf" /etc/systemd/sleep.conf.d/80-ceh-lab-no-sleep.conf
"${admin[@]}" systemctl mask "${targets[@]}"
for target in "${targets[@]}"; do
    state="$(systemctl is-enabled "$target" 2>/dev/null || true)"
    [[ "$state" == masked ]] || { echo "Failed to mask $target" >&2; exit 1; }
    printf '%s: %s\n' "$target" "$state"
done
echo 'PASS: guest suspend/hibernate blocked immediately and persistently.'
echo 'No desktop/logind restart was performed. Drop-ins also apply to future service starts.'
echo 'The physical Hyper-V host must remain awake for any VM to keep running.'
