"""Config flow for the Cooking BLE integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import (
    ANOVA_LOCAL_NAME,
    ANOVA_SERVICE_UUID,
    CONF_MODEL,
    DOMAIN,
    H5055A_MANUFACTURER_ID,
    H5055A_SERVICE_UUID,
    MODEL_ANOVA,
    MODEL_H5055A,
)
from .h5055a import parse


def _model(info: BluetoothServiceInfoBleak) -> str | None:
    """Which supported device this is, if any."""
    payload = info.manufacturer_data.get(H5055A_MANUFACTURER_ID)
    if (
        H5055A_SERVICE_UUID in info.service_uuids
        and payload is not None
        and parse(payload) is not None
    ):
        return MODEL_H5055A
    if info.name == ANOVA_LOCAL_NAME and ANOVA_SERVICE_UUID in info.service_uuids:
        return MODEL_ANOVA
    return None


def _title(model: str, address: str) -> str:
    suffix = address[-5:].replace(":", "")
    return f"Govee H5055A {suffix}" if model == MODEL_H5055A else f"Anova {suffix}"


class CookingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._model: str | None = None
        self._discovered: dict[str, str] = {}
        self._models: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a device found by the bluetooth integration."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if (model := _model(discovery_info)) is None:
            return self.async_abort(reason="not_supported")
        self._model = model
        self.context["title_placeholders"] = {
            "name": _title(model, discovery_info.address)
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered device."""
        assert self._model is not None and self.unique_id is not None
        title = _title(self._model, self.unique_id)
        if user_input is not None:
            return self.async_create_entry(title=title, data={CONF_MODEL: self._model})
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders={"name": title}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a device from the ones currently advertising."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered[address],
                data={CONF_MODEL: self._models[address]},
            )

        current = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass, connectable=False):
            if info.address in current or (model := _model(info)) is None:
                continue
            self._discovered[info.address] = _title(model, info.address)
            self._models[info.address] = model
        if not self._discovered:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(self._discovered)}
            ),
        )
