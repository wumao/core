"""Support for Aqara Vacuums."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from aqara_iot import AqaraPoint, AqaraDeviceManager
from . import HomeAssistantAqaraData
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, AQARA_DISCOVERY_NEW

from .base import (
    AqaraEntity,
    find_aqara_device_points_and_register,
    entity_data_update_binding,
)

from homeassistant.components.vacuum import (
    ATTR_FAN_SPEED,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_FAN_SPEED,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_START,
    SUPPORT_STATUS,
    SUPPORT_STOP,
    VacuumEntityDescription,
)


#  1: 清洁 3: 拖地 16: 暂停 2: 充电 0: 停止
ECOVACS_STATUS_TO_HA = {
    "1": STATE_CLEANING,
    "3": STATE_RETURNING,
    "16": STATE_PAUSED,
    "2": STATE_DOCKED,
    "0": STATE_IDLE,
}

STONE_STATUS_TO_HA = {
    # "1": STATE_CLEANING,
    # "3": STATE_RETURNING,
    # "16": STATE_PAUSED,
    # "2": STATE_DOCKED,
    # "0": STATE_IDLE,
    "0": STATE_IDLE,  # 休眠
    "1": STATE_IDLE,  # 待命
    "2": STATE_CLEANING,  # 清扫
    "3": STATE_DOCKED,  # 回充
    # "4": ,#遥控
    "5": STATE_DOCKED,  # 充电
    "6": STATE_PAUSED,  # 暂停
    "7": STATE_CLEANING,  # 局部清扫
    # "8": ,#报错
    # "9": ,#升级
    "10": STATE_RETURNING,  # 回蹭（回充）
    # "11": ,#指哪到哪
    # "12": ,#划区清扫
    # "13": ,#选区清扫
}


STONE_FAN_SPEED = {
    "1": "normal",  # 标准
    "3": "max",
    "4": "soft",
    "2": "force",
    "0": "quite",
}

STONE_CONTROL = {
    "1": "",  # 开始
    "0": "",  # 暂停
    "2": "",  # 继续
    "3": "",  # 回充
}


@dataclass
class AqaraVacuumEntityDescription(VacuumEntityDescription):
    """Describe an Aqara (de)humidifier entity."""

    supported_features: int = 0

    # ecovacs###############################
    switch_nostatus_res_id: str | None = None  # 识别设备 1: 打开
    view_pic_res_id: str | None = None  # 主图片（用于占位 0: 关闭
    switch_ch1_status_res_id: str | None = None
    # 设备状态 设备上报当前状态 1: 清洁 3: 拖地 16: 暂停 2: 充电 0: 停止，包括停止、清洁、充电、拖地、暂停

    ctrl_ch2_mulstatus_res_id: str | None = None  # 控制设备运行  1: 开始 2: 暂停  3: 继续
    switch_nostatus_2_res_id: str | None = None  # 设备充电   1: 充电

    # stone
    device_battery_power_res_id: str | None = None  # 电池电量显示设备当前的电量，范围[]0，100]
    switch_ch4_status_res_id: str | None = None  # 设备状态 设备上报当前状态
    set_device_mode2_res_id: str | None = None  # 1: 开始 0: 暂停  2: 继续 3: 回充
    set_device_mode3_res_id: str | None = None  # 1: 标准 3: MAX 4: 轻柔 2: 强力 0: 安静
    set_device_mode4_res_id: str | None = None  # 0: 零水量 2: 中水量 1: 小水量 3: 大水量


# SUPPORT_TURN_ON = 1
# SUPPORT_TURN_OFF = 2
# SUPPORT_PAUSE = 4
# SUPPORT_START = 8192
# # SUPPORT_STOP = 8
# SUPPORT_RETURN_HOME = 16
# SUPPORT_FAN_SPEED = 32
# SUPPORT_BATTERY = 64
# SUPPORT_STATUS = 128
# SUPPORT_SEND_COMMAND = 256
# SUPPORT_LOCATE = 512
# SUPPORT_CLEAN_SPOT = 1024
# SUPPORT_MAP = 2048
# SUPPORT_STATE = 4096

ecovacs_vacuum = AqaraVacuumEntityDescription(
    key="14.29.85",
    # view_pic_res_id="3.99.85",  # 主图片（用于占位 0: 关闭
    switch_nostatus_res_id="4.7.85",  # 识别设备 1: 打开
    switch_ch1_status_res_id="13.1.85",  # 设备状态 设备上报当前状态 1: 清洁 3: 拖地 16: 暂停 2: 充电 0: 停止，包括停止、清洁、充电、拖地、暂停
    ctrl_ch2_mulstatus_res_id="14.29.85",  # 控制设备运行  1: 开始 2: 暂停  3: 继续
    switch_nostatus_2_res_id="4.41.85",  # 设备充电   1: 充电
    supported_features=SUPPORT_START | SUPPORT_STOP | SUPPORT_PAUSE | SUPPORT_STATUS,
)

stone_vacuum = AqaraVacuumEntityDescription(
    key="14.29.85",
    device_battery_power_res_id="8.0.2001",  # 电池电量显示设备当前的电量，范围[]0，100]
    switch_ch4_status_res_id="13.4.85",  # 设备状态 设备上报当前状态
    set_device_mode2_res_id="14.47.85",  # 1: 开始 0: 暂停  2: 继续 3: 回充
    set_device_mode3_res_id="14.48.85",  # 1: 标准 3: MAX 4: 轻柔 2: 强力 0: 安静
    # set_device_mode4_res_id="",  # 0: 零水量 2: 中水量 1: 小水量 3: 大水量
    supported_features=SUPPORT_START
    | SUPPORT_STOP
    | SUPPORT_PAUSE
    | SUPPORT_STATUS
    | SUPPORT_RETURN_HOME
    | SUPPORT_BATTERY
    | SUPPORT_FAN_SPEED,
)

VACUUM_DESCRIPTIONS: dict[str, AqaraVacuumEntityDescription] = {
    "aqara.swe_rob.decn05": ecovacs_vacuum,  # 科沃斯扫拖洗机器人 X1 TURBO
    "aqara.swe_rob.decn04": ecovacs_vacuum,  # 科沃斯扫拖洗机器人 X1 OMNI
    "aqara.swe_rob.decn02": ecovacs_vacuum,  # 科沃斯扫地机器人 T9 AIVI
    "aqara.swe_rob.decn01": ecovacs_vacuum,  # 科沃斯扫地机器人
    "aqara.swe_rob.stcn02": stone_vacuum,  # 石头扫地机器人S2
    "aqara.swe_rob.stcn01": stone_vacuum,  # 石头扫地机器人
    "miot.rockrobo_vacuum.v1": stone_vacuum,  # 米家扫地机器人
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara vacuum dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara climate."""
        entities: list[AqaraVacuumEntity] = []

        def append_entity(aqara_point, description: AqaraVacuumEntityDescription):
            entity = AqaraVacuumEntity(
                aqara_point, hass_data.device_manager, description
            )
            entities.append(entity)
            res_ids: list[Optional[str]] = [
                description.switch_ch1_status_res_id,
                description.ctrl_ch2_mulstatus_res_id,
                description.switch_nostatus_2_res_id,
                description.device_battery_power_res_id,
                description.switch_ch4_status_res_id,
                description.set_device_mode2_res_id,
                description.set_device_mode3_res_id,
            ]
            entity_data_update_binding(
                hass, hass_data, entity, aqara_point.did, res_ids
            )

        find_aqara_device_points_and_register(
            hass,
            entry.entry_id,
            hass_data,
            device_ids,
            VACUUM_DESCRIPTIONS,
            append_entity,
        )
        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraVacuumEntity(AqaraEntity):
    """Aqara Vacuum Device."""

    entity_description: AqaraVacuumEntityDescription

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraVacuumEntityDescription,
    ) -> None:
        """Init Aqara vacuum."""
        super().__init__(point, device_manager)
        self._attr_supported_features = description.supported_features

    @property
    def battery_level(self) -> int | None:
        """Return Aqara device state."""
        if self.entity_description.device_battery_power_res_id is not None:
            battery_power_value = self.device_manager.get_point_value(
                self.point.did, self.entity_description.device_battery_power_res_id
            )
            if battery_power_value != "":
                return round(battery_power_value)
        return None

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        if self.entity_description.set_device_mode3_res_id is not None:
            value = self.device_manager.get_point_value(
                self.point.did, self.entity_description.set_device_mode3_res_id
            )
            return STONE_FAN_SPEED.get(value, None)
        return None

    @property
    def fan_speed_list(self) -> list[str]:
        """Get the list of available fan speed steps of the vacuum cleaner."""
        if self.entity_description.set_device_mode3_res_id is not None:
            return list(STONE_FAN_SPEED.values())
        return []

    @property
    def state(self) -> str | None:
        """Return Aqara vacuum device state."""
        if self.entity_description.switch_ch1_status_res_id is not None:
            status_value = self.device_manager.get_point_value(
                self.point.did, self.entity_description.switch_ch1_status_res_id
            )
            return ECOVACS_STATUS_TO_HA.get(status_value, None)
        elif self.entity_description.switch_ch4_status_res_id is not None:
            status_value = self.device_manager.get_point_value(
                self.point.did, self.entity_description.switch_ch1_status_res_id
            )
            return STONE_STATUS_TO_HA.get(status_value, None)
        return None

    # @property
    # def supported_features(self) -> int:
    #     """Flag supported features."""
    #     return self._supported_features

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        if self.entity_description.ctrl_ch2_mulstatus_res_id is not None:
            # 控制设备运行  1: 开始 2: 暂停  3: 继续
            self._send_command({self.entity_description.ctrl_ch2_mulstatus_res_id: "1"})
        if self.entity_description.set_device_mode2_res_id is not None:
            # 1: 开始 0: 暂停 2: 继续 3: 回充
            self._send_command({self.entity_description.set_device_mode2_res_id: "1"})

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        if self.entity_description.ctrl_ch2_mulstatus_res_id is not None:
            # 控制设备运行  1: 开始 2: 暂停  3: 继续
            self._send_command({self.entity_description.ctrl_ch2_mulstatus_res_id: "2"})
        if self.entity_description.set_device_mode2_res_id is not None:
            # 1: 开始 0: 暂停 2: 继续 3: 回充
            self._send_command({self.entity_description.set_device_mode2_res_id: "3"})
        return None

    def start(self, **kwargs: Any) -> None:
        """Start the device."""
        if self.entity_description.ctrl_ch2_mulstatus_res_id is not None:
            # 控制设备运行  1: 开始 2: 暂停  3: 继续
            self._send_command({self.entity_description.ctrl_ch2_mulstatus_res_id: "1"})
        if self.entity_description.set_device_mode2_res_id is not None:
            # 1: 开始 0: 暂停 2: 继续 3: 回充
            self._send_command({self.entity_description.set_device_mode2_res_id: "1"})
        return None

    def stop(self, **kwargs: Any) -> None:
        """Stop the device."""
        if self.entity_description.ctrl_ch2_mulstatus_res_id is not None:
            # 控制设备运行  1: 开始 2: 暂停  3: 继续
            self._send_command({self.entity_description.ctrl_ch2_mulstatus_res_id: "2"})
        if self.entity_description.set_device_mode2_res_id is not None:
            # 1: 开始 0: 暂停 2: 继续 3: 回充
            self._send_command({self.entity_description.set_device_mode2_res_id: "3"})
        return None

    def pause(self, **kwargs: Any) -> None:
        """Pause the device."""
        if self.entity_description.ctrl_ch2_mulstatus_res_id is not None:
            # 控制设备运行  1: 开始 2: 暂停  3: 继续
            self._send_command({self.entity_description.ctrl_ch2_mulstatus_res_id: "2"})
        if self.entity_description.set_device_mode2_res_id is not None:
            # 1: 开始 0: 暂停 2: 继续 3: 回充
            self._send_command({self.entity_description.set_device_mode2_res_id: "0"})
        return None

    def return_to_base(self, **kwargs: Any) -> None:
        """Return device to dock."""
        # if self.entity_description.ctrl_ch2_mulstatus_res_id is not None:
        #     # 控制设备运行  1: 开始 2: 暂停  3: 继续
        #     self._send_command(
        #         [{self.entity_description.ctrl_ch2_mulstatus_res_id: "3"}]
        #     )
        if self.entity_description.set_device_mode2_res_id is not None:
            # 1: 开始 0: 暂停 2: 继续 3: 回充
            self._send_command({self.entity_description.set_device_mode2_res_id: "3"})
        return None

    def locate(self, **kwargs: Any) -> None:
        """Locate the device."""
        return None

    def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        if self.entity_description.set_device_mode3_res_id is not None:
            # 1: 标准 3: MAX 4: 轻柔 2: 强力 0: 安静
            for key, value in STONE_FAN_SPEED.items():
                if value == kwargs[ATTR_FAN_SPEED]:
                    self._send_command(
                        {self.entity_description.set_device_mode3_res_id: key}
                    )
        return None
