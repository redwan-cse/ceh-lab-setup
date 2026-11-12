#!/usr/bin/env bash
# Passive local inventory only: no probes, installs, or configuration writes.
set -uo pipefail

fail() { printf 'Host collection failed: %s\n' "$*" >&2; exit 1; }
if [[ $# != 2 || "$1" != --section ]]; then
    printf 'Usage: bash collect-host-parrot.sh --section host|addresses|routes|neighbors|capabilities\n' >&2
    exit 2
fi
section=$2
case "$section" in
    host|addresses|routes|neighbors|capabilities) ;;
    *) printf 'Unknown collection section: %s\n' "$section" >&2; exit 2 ;;
esac

if [[ "$section" == addresses || "$section" == routes || "$section" == neighbors ]]; then
    command -v ip >/dev/null 2>&1 || fail 'Required command missing: ip (iproute2). No changes made.'
fi

case "$section" in
    host)
        host_name=''
        if [[ -r /proc/sys/kernel/hostname ]]; then
            IFS= read -r host_name < /proc/sys/kernel/hostname || :
        elif command -v hostname >/dev/null 2>&1; then
            host_name=$(hostname) || fail 'hostname query failed'
        fi
        [[ -n "$host_name" ]] || fail 'Cannot read the local host name'
        os_name=Linux
        if [[ -r /etc/os-release ]]; then
            # Parse a data field; never source/execute os-release content.
            while IFS= read -r line || [[ -n "$line" ]]; do
                if [[ "$line" == PRETTY_NAME=* ]]; then
                    os_name=${line#PRETTY_NAME=}
                    os_name=${os_name#\"}; os_name=${os_name%\"}
                    os_name=${os_name#\'}; os_name=${os_name%\'}
                    break
                fi
            done < /etc/os-release
        fi
        account=${USER:-${LOGNAME:-unknown}}
        if command -v id >/dev/null 2>&1; then
            account=$(id -un) || fail 'id account query failed'
        fi
        printf 'HostName : %s\nOS : %s\nAccount : %s\n' "$host_name" "$os_name" "$account"
        if [[ -r /proc/sys/kernel/osrelease ]]; then
            IFS= read -r kernel < /proc/sys/kernel/osrelease || :
            printf 'Kernel : %s\n' "$kernel"
        fi
        if [[ -r /proc/uptime ]]; then
            read -r uptime_seconds ignored < /proc/uptime || :
            printf 'UptimeSeconds : %s\n' "$uptime_seconds"
        fi
        ;;
    addresses)
        ip -brief address || fail 'ip -brief address failed'
        ;;
    routes)
        printf 'IPv4 routes:\n'
        ip -4 route show || fail 'ip -4 route show failed'
        printf '\nDNS resolver configuration (/etc/resolv.conf):\n'
        if [[ -r /etc/resolv.conf ]]; then
            dns_found=false
            while IFS= read -r line || [[ -n "$line" ]]; do
                read -r key value <<< "$line"
                case "$key" in
                    nameserver|search|domain) printf '%s %s\n' "$key" "$value"; dns_found=true ;;
                esac
            done < /etc/resolv.conf
            "$dns_found" || printf 'No resolver entries configured.\n'
        else
            printf 'Resolver configuration unavailable.\n'
        fi
        ;;
    neighbors)
        printf 'Cached IPv4 neighbors (no discovery packets sent):\n'
        neighbors=$(ip -4 neighbor show) || fail 'ip -4 neighbor show failed'
        if [[ -n "$neighbors" ]]; then printf '%s\n' "$neighbors"; else printf 'No cached IPv4 neighbors.\n'; fi
        ;;
    capabilities)
        printf 'Core tool availability (commands are not executed):\n'
        for tool in bash ip ss arp route hostname id uname curl wget python3 python pip3 pip sgpt nmap tshark tcpdump openssl ssh nc dig nslookup; do
            if tool_path=$(command -v "$tool" 2>/dev/null); then
                printf '%s : available (%s)\n' "$tool" "$tool_path"
            else
                printf '%s : missing\n' "$tool"
            fi
        done
        ;;
esac
exit 0
