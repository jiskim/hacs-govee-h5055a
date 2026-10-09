"""Base entity for the Anova BLE integration."""

from __future__ import annotations

from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .anova_coordinator import AnovaCoordinator


class AnovaEntity(CoordinatorEntity[AnovaCoordinator]):
    """Shared device info and unit handling."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AnovaCoordinator, key: str) -> None:
        super().__init__(coordinator)
        address = coordinator.address
        self._attr_unique_id = f"{address}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            manufacturer="Anova",
            model="Precision Cooker (Bluetooth)",
            name="Anova",
        )

    @property
    def _unit(self) -> UnitOfTemperature:
        """The cooker reports in whatever unit its display is set to."""
        if self.coordinator.data and self.coordinator.data.unit == "f":
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS
