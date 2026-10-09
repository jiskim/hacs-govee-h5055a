# Govee H5055A

Home Assistant integration for the Govee **H5055A** BBQ thermometer. The
built-in `govee_ble` integration decodes it as an H5055, whose packet layout
is different, and reports nonsense (battery 0 %, probe temperatures in the
thousands).

This integration listens passively to the thermometer's BLE advertisements
from every Bluetooth adapter and ESPHome proxy Home Assistant has.

## Install (HACS)

HACS → ⋮ → Custom repositories → add this repo as type *Integration*,
install **Govee H5055A**, restart Home Assistant. The thermometer is then
discovered automatically, or add it under Settings → Devices & services.

Ignore the same device in `govee_ble` so its broken entities go away.

## Entities

| Entity | Notes |
|---|---|
| Probe 1 / 3 / 5 | °C, unknown when the probe is unplugged |
| Battery | diagnostic |
| Raw packet | diagnostic, disabled by default; hex of the latest payload |

Probes 2, 4 and 6 are not decoded yet; see `parser.py` for the known layout.
