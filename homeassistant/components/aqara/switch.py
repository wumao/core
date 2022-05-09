"""Support for Aqara switches."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from aqara_iot import AqaraPoint, AqaraDeviceManager
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeAssistantAqaraData
from .base import AqaraEntity, find_aqara_device_points_and_register
from .const import DOMAIN, AQARA_DISCOVERY_NEW


@dataclass
class AqaraSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Aqara switch ."""

    # Value to consider binary sensor to be "on"
    on_value: Any = True
    load_power_res_id: str | None = None

    def set_key(self, key) -> AqaraSwitchEntityDescription:
        """Set key of binary Description."""
        self.key = key
        return self

    def set_name(self, name) -> AqaraSwitchEntityDescription:
        """Set name of binary Description."""
        self.name = name
        return self


OUTLET_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.1.85",
    name="switch ",
    device_class=SwitchDeviceClass.OUTLET,
    entity_category=EntityCategory.CONFIG,
)


first_channel_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.1.85",
    name="switch 1",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)

second_channel_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.2.85",
    name="switch 2",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)


third_channel_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.3.85",
    name="switch 3",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)
four_channel_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.4.85",
    name="switch 4",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)
five_channel_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.5.85",
    name="switch 5",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)
six_channel_desc = AqaraSwitchEntityDescription(  # 打开/关闭,0:关闭，1:打开,2:toggle
    key="4.6.85",
    name="switch 6",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)

# 插座
outlet = (OUTLET_desc,)

# 单键开关
one_chann_switch = (first_channel_desc,)

# 双键开关
two_chann_switch = (
    first_channel_desc,
    second_channel_desc,
)

# 三键开关
three_chann_switch = (
    first_channel_desc,
    second_channel_desc,
    third_channel_desc,
)

# 四键开关
four_chann_switch = (
    first_channel_desc,
    second_channel_desc,
    third_channel_desc,
    four_channel_desc,
)

# 六键开关
six_chann_switch = (
    first_channel_desc,
    second_channel_desc,
    third_channel_desc,
    four_channel_desc,
    five_channel_desc,
    six_channel_desc,
)

SWITCHES: dict[str, tuple[AqaraSwitchEntityDescription, ...]] = {}


# 单键：京鱼座智能开关L1系列一键-零火
SWITCHES["lumi.switch.jcn001"] = one_chann_switch
# 单键：智能墙壁开关 H1M（零火线单键版）
SWITCHES["lumi.switch.acn029"] = one_chann_switch
# 单键:智能墙壁开关 H1M（单火线单键版）
SWITCHES["lumi.switch.acn023"] = one_chann_switch


# 双键：智能墙壁开关 H1M（零火线双键版）
SWITCHES["lumi.switch.acn030"] = two_chann_switch
SWITCHES["lumi.ctrl_ln2.aq1"] = two_chann_switch
SWITCHES["lumi.ctrl_ln2.es1"] = two_chann_switch
SWITCHES["lumi.ctrl_ln2.v1"] = two_chann_switch

SWITCHES["lumi.switch.acn024"] = two_chann_switch
SWITCHES["lumi.switch.b2lc04"] = two_chann_switch
SWITCHES["lumi.ctrl_neutral2.es1"] = two_chann_switch

SWITCHES["lumi.switch.b2nacn01"] = two_chann_switch
SWITCHES["lumi.switch.b2nacn02"] = two_chann_switch
SWITCHES["lumi.ctrl_ln2.aq1"] = two_chann_switch
SWITCHES["lumi.switch.n2aeu1"] = two_chann_switch
SWITCHES["lumi.switch.l2aeu1"] = two_chann_switch
SWITCHES["lumi.ctrl_neutral2.aq1"] = two_chann_switch
SWITCHES["lumi.switch.b2lacn02"] = two_chann_switch
SWITCHES["lumi.switch.b2lacn01"] = two_chann_switch
SWITCHES["lumi.ctrl_ln2.es1"] = two_chann_switch
SWITCHES["lumi.switch.n2acn1"] = two_chann_switch
SWITCHES["lumi.ctrl_neutral2.v1"] = two_chann_switch
SWITCHES["lumi.remote.b286acn01"] = two_chann_switch
SWITCHES["lumi.sensor_86sw2.aq1"] = two_chann_switch
SWITCHES["lumi.switch.b2naus01"] = two_chann_switch
SWITCHES["lumi.ctrl_ln2.v1"] = two_chann_switch


# 三键：智能墙壁开关 H1M（零火线三键版）
SWITCHES["lumi.switch.acn031"] = three_chann_switch
SWITCHES["lumi.switch.acn028"] = three_chann_switch
SWITCHES["GatewayDeviceCC"] = three_chann_switch
SWITCHES["ZigbeeDeviceCC3"] = three_chann_switch

SWITCHES["lumi.switch.n3acn3"] = three_chann_switch
SWITCHES["lumi.switch.n3acn1"] = three_chann_switch
SWITCHES["lumi.switch.l3acn1"] = three_chann_switch
SWITCHES["lumi.switch.l3acn1"] = three_chann_switch
SWITCHES["lumi.switch.l3acn3"] = three_chann_switch
SWITCHES["lumi.switch.b3n01"] = three_chann_switch
SWITCHES["lumi.switch.b3l01"] = three_chann_switch


# 插座：智能插座T1
SWITCHES["lumi.plug.macn01"] = outlet
# 智能插座（Zigbee版）
SWITCHES["lumi.plug.v1"] = outlet
SWITCHES["lumi.plug.acn003"] = outlet
SWITCHES["lumi.plug.eicn03"] = outlet
SWITCHES["lumi.plug.sgwacn01"] = outlet
SWITCHES["lumi.plug.aq1"] = outlet
SWITCHES["lumi.plug.sacn02"] = outlet
SWITCHES["lumi.plug.sacn03"] = outlet
SWITCHES["lumi.plug.maus01"] = outlet
SWITCHES["lumi.plug.es1"] = outlet
SWITCHES["lumi.plug.maeu01"] = outlet


# 集悦妙控屏 S1 Pro 底座
SWITCHES["lumi.switch.acn022"] = three_chann_switch
# 智能温控器 S3-温控器
SWITCHES["lumi.airrtc.pcacn2_thermostat"] = three_chann_switch
# 京鱼座智能开关L1系列三键-零火
SWITCHES["lumi.switch.jcn004"] = three_chann_switch
# 集悦妙控屏 S1 Pro
# SWITCHES["lumi.controller.acn002"] = three_chann_switch


# 智能墙壁开关 H1M（单火线双键版）
SWITCHES["lumi.switch.acn024"] = two_chann_switch
# 智能温控器 S3-场景面板
SWITCHES["lumi.airrtc.pcacn2_scenepanel"] = two_chann_switch
# 京鱼座智能开关L1系列二键-零火
SWITCHES["lumi.switch.jcn002"] = two_chann_switch

# 单路控制模块T1
SWITCHES["lumi.switch.n0agl1"] = one_chann_switch

# 智能墙壁开关 D1 单火线单键版
SWITCHES["lumi.switch.b1lacn02"] = one_chann_switch
# 智能墙壁开关 D1 零火线单键版
SWITCHES["lumi.switch.b1nacn02"] = one_chann_switch

# 智能墙壁开关 D1L 零火线三键版
SWITCHES["lumi.switch.acn015"] = three_chann_switch

# 智能墙壁开关 E1（单火线单键版）
SWITCHES["lumi.switch.b1lc04"] = one_chann_switch

# 智能墙壁开关 E1（单火线双键版）
SWITCHES["lumi.switch.b2lc04"] = two_chann_switch

# 智能墙壁开关 E1（零火线单键版）
SWITCHES["lumi.switch.b1nc01"] = one_chann_switch

# 智能墙壁开关 E1（零火线双键版）
SWITCHES["lumi.switch.b2nc01"] = two_chann_switch

# 欧标智能墙壁开关（零火线双键版
SWITCHES["lumi.switch.n2aeu1"] = two_chann_switch

# 欧标智能墙壁开关（零火线单键版）
SWITCHES["lumi.switch.n1aeu1"] = one_chann_switch

# 欧标智能墙壁开关（单火线双键版）
SWITCHES["lumi.switch.l2aeu1"] = two_chann_switch

# 欧标智能墙壁开关（单火线单键版）
SWITCHES["lumi.switch.l1aeu1"] = one_chann_switch

# 天朗墙壁开关（零火双键版）
SWITCHES["aqara.switch.n2eic1"] = two_chann_switch

# 天朗墙壁开关（零火六键版）
SWITCHES["lumi.switch.n6eic1"] = six_chann_switch

# 天朗墙壁开关（零火四键版）
SWITCHES["lumi.switch.n4eic1"] = four_chann_switch

# 天朗墙壁开关（零火双键版）
SWITCHES["lumi.switch.n2eic1"] = two_chann_switch
# 天朗墙壁开关（零火三键版）
SWITCHES["lumi.switch.n3eic1"] = three_chann_switch
# 天朗墙壁开关（零火单键版）
SWITCHES["lumi.switch.n1eic1"] = one_chann_switch

# 智能墙壁开关 H1 单火线三键版
SWITCHES["lumi.switch.l3acn1"] = three_chann_switch

# 智能墙壁开关 H1（单火单键）
SWITCHES["lumi.switch.l1acn1"] = one_chann_switch

# lumi.switch.l2acn1
SWITCHES["lumi.switch.l2acn1"] = two_chann_switch
# 智能场景面板开关S1
SWITCHES["lumi.switch.n4acn4"] = three_chann_switch

# 智能温控器 S3
SWITCHES["lumi.airrtc.pcacn2"] = three_chann_switch
# 酒店插卡取电开关
SWITCHES["lumi.switch.n0acn1"] = one_chann_switch
# 智能墙壁开关 H1 零火线三键版
SWITCHES["lumi.switch.n3acn1"] = three_chann_switch
# 智能墙壁开关 H1（零火单键）
SWITCHES["lumi.switch.n1acn1"] = one_chann_switch
# 智能墙壁开关 H1（零火双键）
SWITCHES["lumi.switch.n2acn1"] = two_chann_switch
# 智能墙壁开关 T1 单火线三键版
SWITCHES["lumi.switch.b3l01"] = three_chann_switch
# 墙壁开关 单火双键 韩国版
SWITCHES["lumi.switch.l2akr1"] = two_chann_switch
# 墙壁开关 单火单键 韩国版
SWITCHES["lumi.switch.l1akr1"] = one_chann_switch
# 智能墙壁开关 D1 单火线双键版
SWITCHES["lumi.switch.b2lacn02"] = two_chann_switch
# 智能墙壁开关 D1 零火线单键版
SWITCHES["lumi.switch.b1nacn02"] = two_chann_switch
# 智能墙壁开关 T1（单火双键）
SWITCHES["lumi.switch.b2lacn01"] = one_chann_switch
# 智能墙壁开关 T1（单火单键）
SWITCHES["lumi.switch.b1lacn01"] = one_chann_switch
# 智能墙壁开关 T1（零火双键）
SWITCHES["lumi.switch.b2nacn01"] = two_chann_switch
# 智能墙壁开关 T1（零火单键）
SWITCHES["lumi.switch.b1nacn01"] = one_chann_switch
# 墙壁开关（单火线单键版）
SWITCHES["lumi.switch.b1laus01"] = one_chann_switch
# 墙壁开关（零火线双键版）
SWITCHES["lumi.switch.b2naus01"] = two_chann_switch
# 墙壁开关（单火线双键版）
SWITCHES["lumi.switch.b2laus01"] = two_chann_switch
# 墙壁开关（零火线单键版
SWITCHES["lumi.switch.b1naus01"] = one_chann_switch

# 墙壁开关（贴墙式单键版）
SWITCHES["lumi.ctrl_neutral1.es1"] = one_chann_switch
# 墙壁开关（贴墙式单键版）
SWITCHES["lumi.ctrl_neutral1.v1"] = two_chann_switch
# 墙壁开关（贴墙式双键版）
SWITCHES["lumi.ctrl_neutral2.v1"] = two_chann_switch
# 墙壁开关（贴墙式单键版）
SWITCHES["lumi.ctrl_neutral1.es1"] = one_chann_switch
# 墙壁开关（贴墙式双键版）
SWITCHES["lumi.ctrl_neutral2.es1"] = two_chann_switch
# 墙壁开关（贴墙式单键版）
SWITCHES["lumi.ctrl_neutral1.aq1"] = one_chann_switch
# 墙壁开关（零火线单键版）
SWITCHES["lumi.ctrl_ln1.v1"] = one_chann_switch
# 墙壁开关（零火线双键版）
SWITCHES["lumi.ctrl_ln2.v1"] = two_chann_switch
# 墙壁开关（零火线单键版）
SWITCHES["lumi.ctrl_ln1.es1"] = one_chann_switch
# 墙壁开关（零火线双键版）
SWITCHES["lumi.ctrl_ln2.es1"] = two_chann_switch
# 墙壁开关（零火线单键版）
SWITCHES["lumi.ctrl_ln1.aq1"] = two_chann_switch
# 墙壁开关（零火线双键版）
SWITCHES["lumi.ctrl_ln2.aq1"] = two_chann_switch

# 单路控制模块 J1（零火线版）
SWITCHES["lumi.switch.eicn03"] = one_chann_switch
# 单路控制模块 J1（单火线版）
SWITCHES["lumi.switch.eicn02"] = one_chann_switch
# 单路控制模块 T1 单火版 海外版本
SWITCHES["lumi.switch.l0agl1"] = one_chann_switch
# 单路控制模块 T1 零火版 海外版本
SWITCHES["lumi.switch.n0agl1"] = one_chann_switch
# 单路控制模块 T1 零火版
SWITCHES["lumi.switch.n0acn2"] = one_chann_switch
# 单路控制模块 T1 单火版
SWITCHES["lumi.switch.l0acn1"] = one_chann_switch
# 双路控制模块
SWITCHES["lumi.ctrl_dualchn.aq1"] = two_chann_switch
# 双路控制模块
SWITCHES["lumi.ctrl_dualchn.v1"] = one_chann_switch
# 双路控制模块
SWITCHES["lumi.ctrl_dualchn.es1"] = one_chann_switch
SWITCHES["lumi.relay.c2acn01"] = two_chann_switch  # 双路控制模块
SWITCHES["lumi.relay.c4acn01"] = four_chann_switch  # 四路控制模块


SWITCHES["lumi.plug.acn003"] = outlet  # Aqara智能墙壁插座 X1
SWITCHES["lumi.plug.eicn03"] = outlet  # 智能插座 J1

SWITCHES["lumi.plug.eicn01"] = outlet  # 智能墙壁插座 J1
SWITCHES["lumi.plug.acn002"] = outlet  # Aqara智能插座 X1
SWITCHES["lumi.plug.sacn03"] = outlet  # Aqara 86 型智能墙壁插座H1
SWITCHES["lumi.gateway.sacn01"] = outlet  # 智能USB墙壁插座 H1（网关版）
SWITCHES["lumi.plug.makr01"] = outlet  # 智能插座T1 韩国版
SWITCHES["lumi.plug.mmeu01"] = outlet  # 米家智能插座（欧标）
SWITCHES["lumi.plug.sacn02"] = outlet  # 智能墙壁插座T1
SWITCHES["lumi.plug.maeu01"] = outlet  # Aqara智能插座T1（欧标）
SWITCHES["lumi.plug.macn01"] = outlet  # Aqara智能插座 T1
SWITCHES["miot.powerstrip.qmi_v1"] = outlet  # 青米智能插排(qmi.powerstrip.v1)
SWITCHES["lumi.plug.mitw01"] = outlet  # 米家智慧插座
SWITCHES["miot.powerstrip.v2"] = outlet  # 米家智能插线板(zimi.powerstrip.v2)
SWITCHES["lumi.plug.aq1"] = outlet  # 智能插座（Zigbee版）
SWITCHES["lumi.plug.sgwacn01"] = outlet  # 墙壁插座（网关版）
SWITCHES["lumi.plug.maus01"] = outlet  # 智能插座（Zigbee版）
SWITCHES["lumi.plug.es1"] = outlet  # 智能插座（Zigbee版）
SWITCHES["lumi.plug.v1"] = outlet  # 智能插座（Zigbee版）
SWITCHES["lumi.ctrl_86plug.aq1"] = outlet  # 墙壁插座（Zigbee版）
SWITCHES["lumi.ctrl_86plug.v1"] = outlet  # 墙壁插座（Zigbee版）
SWITCHES["lumi.ctrl_86plug.es1"] = outlet  # 墙壁插座（Zigbee版）


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up aqara sensors dynamically through aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered aqara sensor."""
        entities: list[AqaraSwitchEntity] = []

        def append_entity(aqara_point, description):
            entities.append(
                AqaraSwitchEntity(aqara_point, hass_data.device_manager, description)
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, SWITCHES, append_entity
        )
        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraSwitchEntity(AqaraEntity, SwitchEntity):
    """Aqara Switch Device."""

    entity_description: AqaraSwitchEntityDescription

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraSwitchEntityDescription,
    ) -> None:
        """Init AqaraHaSwitch."""
        super().__init__(point, device_manager)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.point.get_value() == "1"

    @property
    def current_power_w(self) -> float | None:
        """Return the current power usage in W."""
        if self.entity_description.load_power_res_id is not None:
            value = self.device_manager.get_point_value(
                self.point.did, self.entity_description.load_power_res_id
            )
            if value != "":
                return float(value)
        return self.current_power_w

    @property
    def today_energy_kwh(self) -> float | None:
        """Return the today total energy usage in kWh."""

        return 0

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._send_command({self.point.resource_id: "1"})

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._send_command({self.point.resource_id: "0"})
