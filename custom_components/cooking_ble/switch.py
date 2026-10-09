"""Start / stop the cooker."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CookingConfigEntry
from .anova_entity import AnovaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CookingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the run switch."""
    async_add_entities([AnovaRunning(entry.runtime_data, "running")])


class AnovaRunning(AnovaEntity, SwitchEntity):
    """On = heating and circulating."""

    _attr_translation_key = "running"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.running if self.coordinator.data else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_command(
            self.coordinator.client.set_running(True), running=True
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_command(
            self.coordinator.client.set_running(False), running=False
        )
