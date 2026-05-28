"""Sensor platform for East Suffolk Bins."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BinCollectionCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BinCollectionCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BinCollectionDataSensor(coordinator, entry),
        BinsDueTodaySensor(coordinator, entry),
        BinsDueTomorrowSensor(coordinator, entry),
    ])


class _BinSensorBase(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: BinCollectionCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def _data(self) -> dict:
        return self.coordinator.data or {}


class BinCollectionDataSensor(_BinSensorBase):
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator: BinCollectionCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_data"
        self._attr_name = "Bin Collection Data"

    @property
    def native_value(self) -> str | None:
        return self._data.get("today")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "collections": self._data.get("collections", []),
            "today": self._data.get("today"),
            "tomorrow": self._data.get("tomorrow"),
            "error": self._data.get("error"),
            "fetched_at": self._data.get("today"),
        }


class BinsDueTodaySensor(_BinSensorBase):
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator: BinCollectionCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_today"
        self._attr_name = "Bins Due Today"

    def _due(self) -> list[dict]:
        cols = self._data.get("collections", [])
        today = self._data.get("today", "")
        return [c for c in cols if c.get("date") == today]

    @property
    def native_value(self) -> str:
        due = self._due()
        return ", ".join(c["label"] for c in due) if due else "None"

    @property
    def extra_state_attributes(self) -> dict:
        due = self._due()
        return {"collections": due, "count": len(due)}


class BinsDueTomorrowSensor(_BinSensorBase):
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, coordinator: BinCollectionCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_tomorrow"
        self._attr_name = "Bins Due Tomorrow"

    def _due(self) -> list[dict]:
        cols = self._data.get("collections", [])
        tomorrow = self._data.get("tomorrow", "")
        return [c for c in cols if c.get("date") == tomorrow]

    @property
    def native_value(self) -> str:
        due = self._due()
        return ", ".join(c["label"] for c in due) if due else "None"

    @property
    def extra_state_attributes(self) -> dict:
        due = self._due()
        return {"collections": due, "count": len(due)}
