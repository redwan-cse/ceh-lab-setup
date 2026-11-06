# Android-8.1-Target — Mobile Target (ADB)

This is the Android VM built by following the supplied
[Gemini Hyper-V guide](reference/gemini-hyper-v-guide.md), section 4.

| Setting | Verified value |
|---|---|
| Hyper-V VM name | Android-8.1-Target |
| Role | Mobile Target (ADB) |
| Guest release | Android 8.1.0 |
| VM generation / resources | Generation 1, 2 vCPUs, 2 GiB RAM |
| Virtual switch | CEH-Lab-Switch (Internal) |
| Guest interface | wifi_eth |
| Address / prefix | 10.10.10.9/24 |
| Gateway | 10.10.10.1 |
| Observed DNS property | net.dns1=8.8.8.8 |
| ADB listener | TCP/5555 |

The original procedure used android-x86_64-8.1-r6.iso, a BIOS/Generation 1 VM,
an ext4 installation with GRUB and a writable system partition. It bypassed the
VirtWifi DHCP loop by configuring wifi_eth manually. These are this image's
setup details, not requirements for every Android version or hypervisor.

## Connect from Parrot

```bash
adb connect 10.10.10.9:5555
adb devices
adb -s 10.10.10.9:5555 shell
```

The device list should show `10.10.10.9:5555 device`. In its shell, inspect:

```sh
getprop ro.build.version.release
ip -4 addr show
ip route
getprop service.adb.tcp.port
getprop net.dns1
```

During verification these returned Android 8.1.0, wifi_eth 10.10.10.9/24,
gateway 10.10.10.1, ADB port 5555 and DNS property 8.8.8.8. A TCP connection
alone is not the same check as a working ADB shell; both were verified.

## Recovery performed on 2026-11-06

Android initially had a running VM on the correct switch but no reachable .9
address. After the user's approval, the local recovery helper:

1. Created current-state checkpoint `before-adb-recovery-20261106-135746-13dca2`.
2. Restored `Android-8.1-Target - adb - (11/5/2026 - 8:06:13 PM)`.
3. Confirmed the VM was Running and host TCP/5555 accepted connections.
4. Was followed by successful `adb connect`, `adb devices` and shell checks
   from Parrot. No other VM was checkpoint-restored.

The [recovery helper](Restore-AndroidAdbCheckpoint.ps1) is inspect-only by
default and must run on physical Redwan-PC in Administrator PowerShell:

```powershell
cd J:\MyProjects\ceh-lab-setup
.\ceh-local-lab\Restore-AndroidAdbCheckpoint.ps1
```

Its explicit `-RestoreAdbCheckpoint` switch saves current state before restoring
the older checkpoint. This rewinds Android's disk and memory: review the change
and preserve work before using it again. Do not restore blindly every session.

## If .9 or ADB disappears after reboot

1. Confirm Android is Running and still uses CEH-Lab-Switch.
2. In its VM console press Alt+F1 for the Android root console; Alt+F7 returns
   to the GUI. Inspect `ip link`, `ip addr` and `ip route`.
3. If the manual state was lost, follow the original guide's image-specific
   wifi_eth/DNS/adbd procedure, after confirming the interface name.
4. Repeat the ADB checks above before creating a new known-working checkpoint.

ADB TCP/5555 is an intentional local training interface. Keep this target on
the internal lab network rather than forwarding it to a public interface.
