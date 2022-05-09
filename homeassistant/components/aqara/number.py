"""Support for Aqara number."""
from __future__ import annotations
from dataclasses import dataclass
from aqara_iot import AqaraPoint, AqaraDeviceManager
from aqara_iot.device import ValueRange
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeAssistantAqaraData
from .base import IntegerTypeData, AqaraEntity, find_aqara_device_points_and_register
from .const import DOMAIN, AQARA_DISCOVERY_NEW


@dataclass
class AqaraNumberEntityDescription(NumberEntityDescription):
    """Describes Aqara Number entity."""

    scale: float = 1
    precision: int = 1
    data_type: str | None = None
    min_value: int = 0
    max_value: int = 100
    step: float = 1

    def set_key(self, key) -> AqaraNumberEntityDescription:
        """Set key of sensor Description."""
        self.key = key
        return self

    def set_name(self, name) -> AqaraNumberEntityDescription:
        """Set name of sensor Description."""
        self.name = name
        return self


common_desc = AqaraNumberEntityDescription(  # 最小值: -4000 最大值: 12500 步长: 1 单位: 62
    key="0.1.85",
    name="Current Temperature",
    data_type="Integer",
    min_value=1,
    max_value=60,
    scale=0.01,
    step=1,
    precision=1,
)

NUMBERS: dict[str, tuple[NumberEntityDescription, ...]] = {
    "aqara.bed.hhcn03": (  # 智能电动床W1
        AqaraNumberEntityDescription(  # 背部升降调节 set_num_third
            key="14.48.85",
            name="背部升降调节",
            data_type="Int",
            min_value=0,
            max_value=60,
            scale=1,
            step=1,
            precision=0,
        ),
        AqaraNumberEntityDescription(  # 腿部升降调节 set_num_fourth
            key="14.93.85",
            name="腿部升降调节",
            data_type="Int",
            min_value=0,
            max_value=40,
            scale=1,
            step=1,
            precision=0,
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara number dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara number."""
        entities: list[AqaraNumberEntity] = []

        def append_entity(aqara_point, description):
            entities.append(
                AqaraNumberEntity(aqara_point, hass_data.device_manager, description)
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, NUMBERS, append_entity
        )

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraNumberEntity(AqaraEntity, NumberEntity):
    """Aqara Number Entity."""

    _status_range: ValueRange | None = None
    _type_data: IntegerTypeData | None = None

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraNumberEntityDescription,
    ) -> None:
        """Init Aqara sensor."""
        super().__init__(point, device_manager)
        self.entity_description = description

        self._type_data = IntegerTypeData(
            min=description.min_value,
            max=description.max_value,
            scale=description.scale,
            step=description.step,
            type=description.data_type,
        )

    @property
    def value(self) -> float | None:
        """Return the entity value to represent the entity state."""
        value = float(self.point.get_value())
        if value is not None and isinstance(self._type_data, IntegerTypeData):
            return self._type_data.scale_value(value)

        return None

    def set_value(self, value: float) -> None:
        """Set new value."""
        if self._type_data is None:
            raise RuntimeError("Cannot set value, device doesn't provide type data")

        self._send_command(
            {self.point.resource_id: str(self._type_data.scale_value_back(value))}
        )
