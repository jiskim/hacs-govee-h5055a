"""Bluetooth cooking thermometers and cookers.

- Govee H5055A BBQ thermometer: decoded from passive advertisements.
- Anova Precision Cooker (classic Bluetooth model): polled over a connection.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .anova_client import AnovaClient
from .anova_coordinator import AnovaCoordinator
from .const import CONF_MODEL, H5055A_MANUFACTURER_ID, MODEL_ANOVA, SIGNAL_UPDATE
from .h5055a import parse

PLATFORMS = {
    MODEL_ANOVA: [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH],
}
DEFAULT_PLATFORMS = [Platform.SENSOR]


@dataclass
class H5055AData:
    """Latest decoded values for one thermometer."""

    address: str
    values: dict[str, float | int | str | None] = field(default_factory=dict)
    available: bool = False


type CookingConfigEntry = ConfigEntry[H5055AData | AnovaCoordinator]


def _platforms(entry: ConfigEntry) -> list[Platform]:
    return PLATFORMS.get(entry.data.get(CONF_MODEL), DEFAULT_PLATFORMS)


async def async_setup_entry(hass: HomeAssistant, entry: CookingConfigEntry) -> bool:
    """Set up one device."""
    if entry.data.get(CONF_MODEL) == MODEL_ANOVA:
        await _setup_anova(hass, entry)
    else:
        _setup_h5055a(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, _platforms(entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CookingConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _platforms(entry))


async def _setup_anova(hass: HomeAssistant, entry: CookingConfigEntry) -> None:
    """Poll the cooker; it may be off, so a failed first read is fine."""
    device = bluetooth.async_ble_device_from_address(
        hass, entry.unique_id, connectable=True
    )
    if device is None:
        raise ConfigEntryNotReady("Anova not in range of any connectable adapter or proxy")
    coordinator = AnovaCoordinator(hass, entry, AnovaClient(device))
    await coordinator.async_refresh()
    entry.runtime_data = coordinator


def _setup_h5055a(hass: HomeAssistant, entry: CookingConfigEntry) -> None:
    """Listen for the thermometer's advertisements from every BLE source."""
    address: str = entry.unique_id
    data = entry.runtime_data = H5055AData(address)
    signal = SIGNAL_UPDATE.format(address)

    @callback
    def _process(service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        payload = service_info.manufacturer_data.get(H5055A_MANUFACTURER_ID)
        if payload is None or (parsed := parse(payload)) is None:
            return
        data.values.update(parsed)
        data.available = True
        async_dispatcher_send(hass, signal)

    @callback
    def _on_advertisement(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        _process(service_info)

    @callback
    def _on_unavailable(service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        data.available = False
        async_dispatcher_send(hass, signal)

    if last := bluetooth.async_last_service_info(hass, address, connectable=False):
        _process(last)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _on_advertisement,
            bluetooth.BluetoothCallbackMatcher(address=address, connectable=False),
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )
    entry.async_on_unload(
        bluetooth.async_track_unavailable(
            hass, _on_unavailable, address, connectable=False
        )
    )
