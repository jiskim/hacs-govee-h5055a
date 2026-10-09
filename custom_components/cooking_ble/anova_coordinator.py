"""Poll the cooker on a timer."""

from __future__ import annotations

import logging

from bleak.exc import BleakError
from bleak_retry_connector import BleakNotFoundError

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .anova_client import AnovaClient, AnovaError, AnovaState
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AnovaCoordinator(DataUpdateCoordinator[AnovaState]):
    """Reads the cooker every UPDATE_INTERVAL; commands refresh right after."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: AnovaClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.address: str = entry.unique_id
        self.client = client

    async def _async_update_data(self) -> AnovaState:
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            raise UpdateFailed("cooker not in range of any connectable adapter or proxy")
        self.client.set_device(device)
        try:
            return await self.client.read_state()
        except (BleakError, BleakNotFoundError, AnovaError, TimeoutError) as err:
            raise UpdateFailed(str(err)) from err
