"""Govee H5055A BBQ thermometer, decoded from passive BLE advertisements."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import MANUFACTURER_ID, SIGNAL_UPDATE
from .parser import parse

PLATFORMS = [Platform.SENSOR]


@dataclass
class H5055AData:
    """Latest decoded values for one thermometer."""

    address: str
    values: dict[str, float | int | str | None] = field(default_factory=dict)
    available: bool = False


type H5055AConfigEntry = ConfigEntry[H5055AData]


async def async_setup_entry(hass: HomeAssistant, entry: H5055AConfigEntry) -> bool:
    """Listen for the thermometer's advertisements from every BLE source."""
    address: str = entry.unique_id
    data = entry.runtime_data = H5055AData(address)
    signal = SIGNAL_UPDATE.format(address)

    @callback
    def _process(service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        payload = service_info.manufacturer_data.get(MANUFACTURER_ID)
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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: H5055AConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
