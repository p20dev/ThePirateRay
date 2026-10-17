# Live USB enumeration — 2026-10-17

## Scope and safety boundary

The JPT fiber laser controller was powered through the machine's normal
procedure and connected by USB to the development computer. Inspection was
limited to Windows' existing Plug and Play database using `Get-PnpDevice`,
`Get-PnpDeviceProperty`, CIM, and `pnputil /enum-devices`.

No application opened the USB device. No endpoint was claimed, no driver was
installed or changed, and no bytes or controller commands were sent. There
was no framing, galvo motion, marking, or laser output.

The complete Windows instance ID contains a device-specific suffix. That
suffix is deliberately omitted from this public record.

## Sanitized observation

| Property | Observed value |
| --- | --- |
| Bus-reported description | `USBLMCV4` |
| USB VID | `9588` |
| USB PID | `9899` |
| USB device revision descriptor | `0005` |
| Compatible class | `FF` — vendor-specific |
| Subclass / protocol | `00` / `00` |
| Windows presence | Present |
| Bound function driver | None |
| Windows problem | Code 28, `CM_PROB_FAILED_INSTALL` |
| Windows explanation | No compatible driver is installed |
| Reboot required | No |

`REV_0005` is the USB device revision descriptor (`bcdDevice`-derived
hardware ID). It must not be relabeled as board revision or firmware version
without independent evidence.

## Interpretation

This is the first live confirmation that the connected physical controller
enumerates with the same `9588:9899` identity found in the private installer
metadata. It also matches the constants used by MeerK40t BalorMK's independent
USB implementation. The three independent observations make BalorMK a strong
compatibility candidate:

1. private JCZ driver metadata from the known installer snapshot;
2. Windows enumeration of the connected controller;
3. BalorMK source code targeting the same VID/PID.

The friendly name `USBLMCV4` is additional evidence about the controller
generation, but it does not by itself prove every command, source parameter,
correction setting, or safety behavior is compatible.

Problem code 28 is expected on this development computer because neither the
vendor driver nor a libusb function driver is installed. It does not indicate
that Windows rejected a known driver or that the controller failed to
enumerate. No attempt was made to fix it because installing libusb could
affect which software can own the controller.

## Consequences

- Change the public machine profile's VID/PID status from inferred installer
  metadata to live-confirmed.
- Retain `Lmcv2u` only as the stock-driver family observed in the installer,
  not as the driver currently bound on this computer.
- Use `9588:9899` as an explicit allow-list identity in future test plans, but
  never as the only machine/profile safety check.
- Keep the next experiment offline. The first controller experiment remains a
  mock trace, not a live USB connection.
- Before any later live connection, choose and document a reversible Windows
  driver strategy and preserve the current production computer's driver state.

## Related sources

- [Sanitized machine profile](machine-profile.yaml)
- [Open-source landscape](open-source-landscape.md)
- [BalorMK USB implementation](https://github.com/meerk40t/meerk40t/blob/main/meerk40t/balormk/usb_connection.py)

