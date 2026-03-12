"""Sensor platform for enisyst Wallbox."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, DOMAIN
from .coordinator import EnisystCoordinator


@dataclass(frozen=True, kw_only=True)
class EnisystSensorEntityDescription(SensorEntityDescription):
    """Describes an enisyst sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[EnisystSensorEntityDescription, ...] = (
    EnisystSensorEntityDescription(
        key="status",
        translation_key="status",
        name="Status",
        icon="mdi:ev-station",
        value_fn=lambda d: d.get("status"),
    ),
    EnisystSensorEntityDescription(
        key="status_text",
        translation_key="status_text",
        name="Status Text",
        icon="mdi:information-outline",
        value_fn=lambda d: d.get("statusText"),
    ),
    EnisystSensorEntityDescription(
        key="power",
        translation_key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("power"),
    ),
    EnisystSensorEntityDescription(
        key="current",
        translation_key="current",
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("current"),
    ),
    EnisystSensorEntityDescription(
        key="cm_current",
        translation_key="cm_current",
        name="Charging Management Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("cm_current"),
    ),
    EnisystSensorEntityDescription(
        key="max_current",
        translation_key="max_current",
        name="Max Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("maxCurrent"),
    ),
    EnisystSensorEntityDescription(
        key="min_current",
        translation_key="min_current",
        name="Min Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("minCurrent"),
    ),
    EnisystSensorEntityDescription(
        key="charged_energy",
        translation_key="charged_energy",
        name="Charged Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.get("chargedEnergy"),
    ),
    EnisystSensorEntityDescription(
        key="charging_time",
        translation_key="charging_time",
        name="Charging Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("chargingTime"),
    ),
    EnisystSensorEntityDescription(
        key="mode",
        translation_key="mode",
        name="Charging Mode",
        icon="mdi:tune",
        value_fn=lambda d: d.get("mode"),
    ),
    EnisystSensorEntityDescription(
        key="enabled",
        translation_key="enabled",
        name="Enabled",
        icon="mdi:power",
        value_fn=lambda d: d.get("enabled"),
    ),
    EnisystSensorEntityDescription(
        key="ocpp_connected",
        translation_key="ocpp_connected",
        name="OCPP Connected",
        icon="mdi:connection",
        value_fn=lambda d: d.get("ocppConnected"),
    ),
    EnisystSensorEntityDescription(
        key="modbus_connected",
        translation_key="modbus_connected",
        name="Modbus Connected",
        icon="mdi:connection",
        value_fn=lambda d: d.get("modbusConnected"),
    ),
    EnisystSensorEntityDescription(
        key="firmware",
        translation_key="firmware",
        name="Firmware",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("firmware"),
    ),
    EnisystSensorEntityDescription(
        key="regulation_reason",
        translation_key="regulation_reason",
        name="Regulation Reason",
        icon="mdi:information",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("regulationReason"),
    ),
    EnisystSensorEntityDescription(
        key="user_id",
        translation_key="user_id",
        name="Active User ID",
        icon="mdi:account",
        value_fn=lambda d: d.get("userId") or None,
    ),
    EnisystSensorEntityDescription(
        key="plug_and_charge",
        translation_key="plug_and_charge",
        name="Plug & Charge",
        icon="mdi:ev-plug-type2",
        value_fn=lambda d: d.get("plugAndCharge"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up enisyst sensors from a config entry."""
    coordinator: EnisystCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id: str = entry.data[CONF_STATION_ID]

    entities: list[EnisystSensorEntity] = []
    for serial, charger_data in coordinator.data.items():
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                EnisystSensorEntity(
                    coordinator=coordinator,
                    description=description,
                    serial=serial,
                    station_id=station_id,
                    charger_name=charger_data.get("Bezeichnung", serial),
                )
            )

    async_add_entities(entities)


class EnisystSensorEntity(CoordinatorEntity[EnisystCoordinator], SensorEntity):
    """Represents a single sensor for one enisyst charger."""

    entity_description: EnisystSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EnisystCoordinator,
        description: EnisystSensorEntityDescription,
        serial: str,
        station_id: str,
        charger_name: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._serial = serial
        self._station_id = station_id
        self._attr_unique_id = f"{station_id}_{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=charger_name,
            manufacturer="enisyst / Alfen",
            model=serial,
            sw_version=coordinator.data.get(serial, {}).get("firmware"),
            configuration_url=f"https://eniserv.de/enilyser/{station_id}/",
        )

    @property
    def native_value(self) -> Any:
        """Return the current value from coordinator data."""
        charger_data = self.coordinator.data.get(self._serial, {})
        return self.entity_description.value_fn(charger_data)
