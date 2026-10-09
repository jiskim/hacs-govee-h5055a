# Cooking BLE

Home Assistant integration for Bluetooth cooking gear that the built-in
integrations get wrong or don't support:

- **Govee H5055A** BBQ thermometer. `govee_ble` decodes it as an H5055, whose
  packet layout is different, and reports nonsense. This integration listens
  passively to its advertisements from every Bluetooth adapter and ESPHome proxy.
- **Anova Precision Cooker, classic Bluetooth model** (advertises as `Anova`,
  service `FFE0`). Not the Wi-Fi models (use the core `anova` integration) and
  not the Nano. The cooker accepts one connection at a time, so this connects
  every 30 s, reads, and disconnects, leaving gaps for the Anova app.

## Install (HACS)

HACS → ⋮ → Custom repositories → add this repo as type *Integration*,
install **Cooking BLE**, restart Home Assistant. Devices are discovered
automatically, or add them under Settings → Devices & services.

Ignore the H5055A in `govee_ble` so its broken entities go away.

## Entities

| Device | Entity | Notes |
|---|---|---|
| H5055A | Probe 1 – 6 | °C, unavailable when the probe is unplugged |
| H5055A | Battery | diagnostic |
| H5055A | Raw packet | diagnostic, disabled by default |
| Anova | Water temperature | in the cooker's display unit |
| Anova | Target temperature | settable |
| Anova | Running | switch: start / stop |

See `h5055a.py` and `anova_client.py` for the protocols.
