"""Support for Aqara binary sensors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aqara_iot import AqaraDeviceManager, AqaraPoint

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import HomeAssistantAqaraData
from .base import AqaraEntity, find_aqara_device_points_and_register
from .const import AQARA_DISCOVERY_NEW, DOMAIN, AQARA_BATTERY_LOW_ENTITY_NEW


@dataclass
class AqaraBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Aqara binary sensor."""

    # Value to consider binary sensor to be "on"
    on_value: Any = True
    on_icon: str = "mdi:restart"
    off_icon: str = "mdi:restart"

    def set_key(self, key) -> AqaraBinarySensorEntityDescription:
        """Set key of binary Description."""
        self.key = key
        return self

    def set_name(self, name) -> AqaraBinarySensorEntityDescription:
        """Set name of binary Description."""
        self.name = name
        return self

    def set_icon(
        self, default_icon: str, on_icon: str, off_icon: str
    ) -> AqaraBinarySensorEntityDescription:
        """Set name of binary Description."""
        self.icon = default_icon
        self.on_icon = on_icon
        self.off_icon = off_icon
        return self


battery_staus_desc = AqaraBinarySensorEntityDescription(  # 电池电量情况，1低电量，0恢复电量
    key="8.0.9001",
    name="电池电量情况",
    icon="mdi:battery",
    entity_category=EntityCategory.DIAGNOSTIC,
    on_value="1",
    device_class=BinarySensorDeviceClass.BATTERY,
)


motion_desc = AqaraBinarySensorEntityDescription(  # 1: 有人
    key="3.1.85",
    name="有人无人状态",
    icon="mdi:account-switch",
    entity_category=EntityCategory.CONFIG,
    on_value="1",
    device_class=BinarySensorDeviceClass.MOTION,
)

# 人体传感器 属性
occupancy_desc = AqaraBinarySensorEntityDescription(  # 0: 无人 1: 有人
    key="3.51.85",
    name="人体存在状态上报",
    icon="mdi:account-question",
    entity_category=EntityCategory.CONFIG,
    on_value="1",
    device_class=BinarySensorDeviceClass.OCCUPANCY,
)

# 窗磁传感器 属性
door_desc = AqaraBinarySensorEntityDescription(  # 0:关 close，1:开  open
    key="3.1.85",
    name="开合状态",
    icon="mdi:restart",
    entity_category=EntityCategory.CONFIG,
    on_value="1",
    device_class=BinarySensorDeviceClass.DOOR,
)

# 水浸传感器 属性
flood_desc = AqaraBinarySensorEntityDescription(  # 0:没漏水,1:漏水
    key="3.1.85",
    name="漏水状态",
    icon="mdi:restart",
    entity_category=EntityCategory.CONFIG,
    on_value="1",
    device_class=BinarySensorDeviceClass.MOISTURE,
)


BINARY_SENSORS: dict[str, tuple[AqaraBinarySensorEntityDescription, ...]] = {
    "lumi.motion.jcn001": (motion_desc, battery_staus_desc),  # 京鱼座人体传感器L版
    "lumi.motion.ac02": (motion_desc, battery_staus_desc),  # 人体传感器 P1
    "lumi.motion.ac01": (occupancy_desc, battery_staus_desc),  # 人体存在传感器 FP1
    "lumi.motion.agl04": (motion_desc, battery_staus_desc),  # 高精度人体传感器
    "lumi.motion.akr01": (motion_desc, battery_staus_desc),  # 人体传感器 T1 韩国版
    "lumi.motion.agl02": (motion_desc, battery_staus_desc),  # 人体传感器 T1
    "lumi.sensor_motion.es2": (motion_desc, battery_staus_desc),  # 人体传感器
    "lumi.sensor_motion.aq2": (motion_desc, battery_staus_desc),  # 人体传感器
    "lumi.sensor_motion.v2": (motion_desc, battery_staus_desc),  # 人体传感器
    "lumi.sensor_motion.v1": (motion_desc, battery_staus_desc),  # 人体传感器
    #############################################################
    "lumi.magnet.acn002": (door_desc, battery_staus_desc),  # 门窗传感器 NB-IOT版
    "lumi.magnet.jcn002": (door_desc, battery_staus_desc),  # 京鱼座门窗传感器L版
    "lumi.magnet.ac01": (door_desc, battery_staus_desc),  # 门窗传感器 P1
    "lumi.magnet.akr01": (door_desc, battery_staus_desc),  # 门窗传感器T1 韩国版
    "lumi.magnet.agl02": (door_desc, battery_staus_desc),  # 门窗传感器T1
    "lumi.sensor_magnet.v1": (door_desc, battery_staus_desc),  # 门窗传感器
    "lumi.sensor_magnet.v2": (door_desc, battery_staus_desc),  # 门窗传感器
    "lumi.sensor_magnet.es2": (door_desc, battery_staus_desc),  # 门窗传感器
    "lumi.sensor_magnet.aq2": (door_desc, battery_staus_desc),  # 门窗传感器
    ##############################################################
    "lumi.flood.jcn001": (flood_desc, battery_staus_desc),  # 京鱼座水浸传感器L版
    "lumi.flood.agl02": (flood_desc, battery_staus_desc),  # 水浸传感器T1
    "lumi.sensor_wleak.v1": (flood_desc, battery_staus_desc),  # 水浸传感器
    "lumi.sensor_wleak.es1": (flood_desc, battery_staus_desc),  # 水浸传感器
    "lumi.sensor_wleak.aq1": (flood_desc, battery_staus_desc),  # 水浸传感器
    #############################################################
    # lock power
    "aqara.lock.acn008": (battery_staus_desc,),  # 低电压报警 8.0.9001 low_battery_power
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara binary sensor dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    def async_add_battery_low_entity(device_id, res_id) -> None:
        """add battery low entity by event. call from other component"""
        aqara_point = hass_data.device_manager.device_map[device_id].point_map.get(
            hass_data.device_manager.make_point_id(device_id, res_id)
        )
        if aqara_point is not None:
            entities: list[AqaraBinarySensorEntity] = [
                AqaraBinarySensorEntity(
                    aqara_point, hass_data.device_manager, battery_staus_desc
                )
            ]
            async_add_entities(entities)

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara binary sensor."""
        entities: list[AqaraBinarySensorEntity] = []

        def append_entity(aqara_point, description):
            entities.append(
                AqaraBinarySensorEntity(
                    aqara_point, hass_data.device_manager, description
                )
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, BINARY_SENSORS, append_entity
        )
        # print(entities)
        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )
    entry.async_on_unload(
        async_dispatcher_connect(
            hass, AQARA_BATTERY_LOW_ENTITY_NEW, async_add_battery_low_entity
        )
    )


class AqaraBinarySensorEntity(AqaraEntity, BinarySensorEntity):
    """Aqara Binary Sensor Entity."""

    entity_description: AqaraBinarySensorEntityDescription

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraBinarySensorEntityDescription,
    ) -> None:
        """Init Aqara binary sensor."""
        super().__init__(point, device_manager)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""
        return (
            self.point.get_value() == self.entity_description.on_value
            or self.point.get_value() in self.entity_description.on_value
        )

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if hasattr(self, "_attr_icon"):
            return self._attr_icon
        if hasattr(self, "entity_description"):
            if self.is_on is True and self.entity_description.on_icon != "":
                return self.entity_description.on_icon
            elif self.is_on is False and self.entity_description.off_icon != "":
                return self.entity_description.off_icon
            else:
                return self.entity_description.icon
        return None
