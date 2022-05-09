"""Support for Aqara siren."""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from aqara_iot import AqaraPoint, AqaraDeviceManager

from homeassistant.components.siren import SirenEntity, SirenEntityDescription
from homeassistant.components.siren.const import SUPPORT_TURN_OFF, SUPPORT_TURN_ON
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeAssistantAqaraData
from .base import AqaraEntity, find_aqara_device_points_and_register
from .const import DOMAIN, AQARA_DISCOVERY_NEW


@dataclass
class AqaraSirenEntityDescription(SirenEntityDescription):
    """Describes a Aqara binary sensor."""

    # Value to consider siren sensor to be "on/off"
    on_value: bool | float | int | str = "1"
    off_value: bool | float | int | str = "0"

    # smoke sensor
    alarm_mute_res_id: str | None = None
    alarm_test_mute_res_id: str | None = None
    ias_sensor_alarm_event_res_id: str | None = None


common_smoke_sensor = AqaraSirenEntityDescription(
    key="8.0.2232",
    name="Siren",
    alarm_mute_res_id="4.12.85",
    alarm_test_mute_res_id="4.15.85",
    ias_sensor_alarm_event_res_id="8.0.2232",
)

gateway_alarm = AqaraSirenEntityDescription(  # 报警状态 14.1.111	 alarm_status
    key="14.1.111",
    name="报警状态",
    alarm_mute_res_id="14.1.111",
    alarm_test_mute_res_id="14.1.111",
    ias_sensor_alarm_event_res_id="14.1.111",
)


SIRENS: dict[str, tuple[SirenEntityDescription, ...]] = {
    # Siren Alarm   smoke
    "lumi.sensor_smoke.acn05": (common_smoke_sensor,),  # Aqara烟雾报警器 X1
    "lumi.sensor_smoke.jcn01": (common_smoke_sensor,),  # 京鱼座烟雾报警器L版
    "lumi.sensor_smoke.acn03": (common_smoke_sensor,),  # Aqara烟雾报警器
    #############################
    # Siren Alarm  gateway
    "lumi.gateway.agl002": (gateway_alarm,),  # 网关 M1S Gen 2
    "lumi.gateway.agl001": (gateway_alarm,),  # 网关 M2 （海外）VE4
    "lumi.gateway.iragl8": (gateway_alarm,),  # 网关 M2 2022款
    "lumi.gateway.acn005": (gateway_alarm,),  # 网关 X2 2022款
    "lumi.camera.agl001": (gateway_alarm,),  # 智能摄像机G2H Pro(海外版)
    "lumi.gateway.acn004": (gateway_alarm,),  # 网关 M1S 2022款（国内版）
    "lumi.camera.acn003": (gateway_alarm,),  # 智能摄像机G2H Pro
    "lumi.camera.akr001": (gateway_alarm,),  # LGU-G3
    "lumi.camera.gwpgl1": (gateway_alarm,),  # 智能摄像机G3（海外版）
    "lumi.acpartner.eicn01": (gateway_alarm,),  # 空调伴侣 J1
    "lumi.plug.eicn02": (gateway_alarm,),  # 智能USB墙壁插座 J1（网关版）
    "lumi.gateway.acn002": (gateway_alarm,),  # 网关 X2
    "lumi.acpartner.acn001": (gateway_alarm,),  # Aqara空调伴侣 X1
    "lumi.camera.gwpagl01": (gateway_alarm,),  # 智能摄像机G3
    "lumi.camera.gwag03": (gateway_alarm,),  # 智能摄像机 G2H（海外版）
    "lumi.gateway.aeu01": (gateway_alarm,),  # 网关 M1S （海外版）
    "lumi.gateway.sacn01": (gateway_alarm,),  # 智能USB墙壁插座 H1（网关版）
    "lumi.gateway.iragl5": (gateway_alarm,),  # 网关 M2（国内版）
    "lumi.aircondition.acn05": (gateway_alarm,),  # 空调伴侣 P3
    "lumi.camera.gwakr1": (gateway_alarm,),  # 智能摄像机 LGU+ G2（网关版）
    "lumi.camera.gwagl02": (gateway_alarm,),  # "智能摄像机 G2H（网关版）"
    "lumi.gateway.acn01": (gateway_alarm,),  # 网关 M1S（国内版）
    "lumi.gateway.irabr01": (gateway_alarm,),  # 网关M2（巴西版）
    "lumi.camera.gwagl01": (gateway_alarm,),  # 智能摄像机 G2（网关版）
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara siren dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara siren."""
        entities: list[AqaraSirenEntity] = []

        def append_entity(aqara_point, description):
            entities.append(
                AqaraSirenEntity(aqara_point, hass_data.device_manager, description)
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, SIRENS, append_entity
        )
        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraSirenEntity(AqaraEntity, SirenEntity):
    """Aqara Siren Entity."""

    entity_description: AqaraSirenEntityDescription

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraSirenEntityDescription,
    ) -> None:
        """Init Aqara Siren."""
        super().__init__(point, device_manager)
        self.entity_description = description
        self._attr_supported_features = SUPPORT_TURN_ON | SUPPORT_TURN_OFF

    @property
    def is_on(self) -> bool:
        """Return true if siren is on."""
        return self.point.get_value() == self.entity_description.on_value

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the siren on."""
        if self.entity_description.alarm_test_mute_res_id is not None:
            self._send_command(
                {
                    self.entity_description.alarm_test_mute_res_id: str(
                        self.entity_description.on_value
                    )
                }
            )
        return None

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the siren off."""
        if self.entity_description.alarm_mute_res_id is not None:
            self._send_command(
                {
                    self.entity_description.alarm_mute_res_id: str(
                        self.entity_description.off_value
                    )
                }
            )

        return None
