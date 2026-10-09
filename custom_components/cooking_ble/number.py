"""Target temperature."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CookingConfigEntry
from .anova_entity import AnovaEntity

# Cooker limits: 0-99 degC, 32-210 degF.
LIMITS = {
    UnitOfTemperature.CELSIUS: (0.0, 99.0),
    UnitOfTemperature.FAHRENHEIT: (32.0, 210.0),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CookingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the target number."""
    async_add_entities([AnovaTarget(entry.runtime_data, "target_temperature")])


class AnovaTarget(AnovaEntity, NumberEntity):
    """Target water temperature."""

    _attr_translation_key = "target_temperature"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_native_step = 0.1

    @property
    def native_unit_of_measurement(self) -> str:
        return self._unit

    @property
    def native_min_value(self) -> float:
        return LIMITS[self._unit][0]

    @property
    def native_max_value(self) -> float:
        return LIMITS[self._unit][1]

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.target if self.coordinator.data else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_command(
            self.coordinator.client.set_target(value), target=round(value, 1)
        )
