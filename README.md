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

## Credits

The H5055A packet layout was worked out from this thermometer's own
advertisements; the original H5055 decoder in
[govee-ble](https://github.com/Bluetooth-Devices/govee-ble) was the starting
point for comparison.

The Anova protocol (service `FFE0`, characteristic `FFE1`, ASCII commands such
as `read temp` / `set temp` / `start` / `stop` terminated by `\r`) comes from
community reverse engineering — no code was copied, but these documented it:

- [neilpa/circulate](https://github.com/neilpa/circulate) — reverse-engineered
  iOS library for the Anova over Bluetooth (MIT), the original protocol reference.
- [erikcw/pycirculate](https://github.com/erikcw/pycirculate) — Python/BlueZ
  wrapper built on circulate's command set.

The "flush the line after connecting" workaround in `anova_client.py` is our
own: it fixes "Invalid Command" answers after quick reconnects.
