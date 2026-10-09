"""Poll the cooker on a timer."""

from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import replace
import logging
from typing import Any

from bleak.exc import BleakError
from bleak_retry_connector import BleakNotFoundError

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .anova_client import AnovaClient, AnovaError, AnovaState
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AnovaCoordinator(DataUpdateCoordinator[AnovaState]):
    """Reads the cooker every UPDATE_INTERVAL; commands update the state directly."""

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

    async def async_command(self, command: Awaitable[None], **changes: Any) -> None:
        """Run a command, then show its effect right away.

        Waiting for a refresh is too slow: the refresh debouncer allows one
        refresh per 10 s, so a quick off-then-on left the switch showing the
        stale state. The cooker answered the command, so trust it; the next
        poll confirms.
        """
        try:
            await command
        except (BleakError, BleakNotFoundError, AnovaError, TimeoutError) as err:
            raise HomeAssistantError(f"Anova did not take the command: {err}") from err
        if self.data is None:
            await self.async_request_refresh()
            return
        self.async_set_updated_data(replace(self.data, **changes))

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
