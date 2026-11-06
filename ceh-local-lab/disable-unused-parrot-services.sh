#!/usr/bin/env bash
# Only for this static-address Hyper-V lab. Tools remain installed.
# Do not use this if you intentionally configured these services for an exercise.
set -euo pipefail
if [[ "$(id -u)" == 0 ]]; then admin=(); else sudo -v; admin=(sudo); fi
for unit in cpupower-gui.service hostapd-wpe.service isc-dhcp-server.service sslh.service; do
    if systemctl is-failed --quiet "$unit"; then
        echo "Disabling failed optional boot service: $unit"
        "${admin[@]}" systemctl disable --now "$unit"
        "${admin[@]}" systemctl reset-failed "$unit"
    else
        echo "Leaving non-failed service unchanged: $unit"
    fi
done
systemctl --failed --no-pager
echo 'Optional tools remain installed; configure and enable a service when an exercise needs it.'
