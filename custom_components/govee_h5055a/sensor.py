"""Sensors for the Govee H5055A."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import H5055AConfigEntry, H5055AData
from .const import DOMAIN, SIGNAL_UPDATE


def _probe(n: int) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=f"probe_{n}",
        translation_key="probe",
        translation_placeholders={"probe": str(n)},
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
    )


DESCRIPTIONS = (
    _probe(1),
    _probe(3),
    _probe(5),
    SensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="raw",
        translation_key="raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: H5055AConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    async_add_entities(
        H5055ASensor(entry.runtime_data, description) for description in DESCRIPTIONS
    )


class H5055ASensor(SensorEntity):
    """One value decoded from the thermometer's advertisements."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, data: H5055AData, description: SensorEntityDescription) -> None:
        self.entity_description = description
        self._data = data
        self._attr_unique_id = f"{data.address}-{description.key}"
        # No bluetooth connection here on purpose: it would merge this device
        # into govee_ble's device for the same address.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.address)},
            manufacturer="Govee",
            model="H5055A",
            name=f"Govee H5055A {data.address[-5:].replace(':', '')}",
        )

    @property
    def available(self) -> bool:
        return self._data.available and self.entity_description.key in self._data.values

    @property
    def native_value(self) -> float | int | str | None:
        return self._data.values.get(self.entity_description.key)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE.format(self._data.address),
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
