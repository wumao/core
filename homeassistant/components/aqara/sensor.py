"""Support for Aqara sensors."""
from __future__ import annotations

from dataclasses import dataclass
from .device_trigger import AQARA_EVENTS_MAP as aqara_events_map

# from typing import Any, cast
import copy
from aqara_iot import AqaraPoint, AqaraDeviceManager

# from aqara_iot import ValueRange
from homeassistant.components.aqara.util import (
    string_dot_to_underline,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ELECTRIC_POTENTIAL_VOLT,
    PERCENTAGE,
    PRESSURE_KPA,
    LIGHT_LUX,
    TEMP_CELSIUS,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import HomeAssistantAqaraData
from .base import (
    DeviceValueRange,
    EnumTypeData,
    IntegerTypeData,
    AqaraEntity,
    find_aqara_device_points_and_register,
)
from .const import (
    DOMAIN,
    AQARA_DISCOVERY_NEW,
    EMPTY_UNIT,
    UnitOfMeasurement,
    AQARA_HA_SIGNAL_UPDATE_POINT_VALUE,
)


@dataclass
class AqaraSensorEntityDescription(SensorEntityDescription):
    """Describes Aqara sensor entity."""

    # value_range: dict[str, Any] | None = None
    # value_range={
    #     "values": '{"min":0,"max":100,"scale":1,"step":1,"unit":""}',
    #     "type": "Integer",
    # },
    scale: float | None = None
    precision: int | None = None
    data_type: str | None = None
    enum_value_map: dict[str, str] | None = None  # dict[str for hass ui, aqara value]
    # native_unit_of_measurement: str | None = EMPTY_UNIT

    def set_key(self, key) -> AqaraSensorEntityDescription:
        """Set key of sensor Description."""
        entity_description = copy.copy(self)
        entity_description.key = key
        return entity_description

    def set_name(self, name) -> AqaraSensorEntityDescription:
        """Set name of sensor Description."""
        self.name = name
        return self

    def set_value_map(self, value_map) -> AqaraSensorEntityDescription:
        self.enum_value_map = value_map
        return self


# Commonly used battery sensors, that are re-used in the sensors down below.
BATTERY_SENSORS: tuple[AqaraSensorEntityDescription, ...] = (
    AqaraSensorEntityDescription(  # 电池电量情况，1低电量, 0:正常
        key="8.0.9001",
        name="Battery State",
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AqaraSensorEntityDescription(
        key="8.0.2008",
        name="电池电压值",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        precision=2,
    ),
)

# # Temperature units
# TEMP_CELSIUS: Final = "°C"
# TEMP_FAHRENHEIT: Final = "°F"
# TEMP_KELVIN: Final = "K"
temp_desc = AqaraSensorEntityDescription(  # 最小值: -4000 最大值: 12500 步长: 1 单位: 62
    key="0.1.85",
    name="Current Temperature",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=TEMP_CELSIUS,
    scale=0.01,
    precision=1,
)
humidity_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 10000 步长: 单位: 29
    key="0.2.85",
    name="Current humidity",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=PERCENTAGE,
    scale=0.01,
    precision=1,
)
co2_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 9999 步长: 1 单位: ppm
    key="0.6.85",
    name="CO2",  # 室内
    device_class=SensorDeviceClass.CO2,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    scale=0.01,
)

pm25_out_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 999 步长: 1 单位: μg/m³
    key="0.19.85",
    name="PM2.5",  # 所在城市室外
    device_class=SensorDeviceClass.PM25,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
)


pm25_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 999 步长: 1 单位: μg/m³
    key="0.20.85",
    name="PM2.5",  # 室内
    device_class=SensorDeviceClass.PM25,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
)
pm25_evaluate_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 999 步长: 1 单位: μg/m³
    key="0.20.85",
    name="PM2.5",  # 室内
    device_class=SensorDeviceClass.PM25,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
)

air_pressure_desc = AqaraSensorEntityDescription(  # 最小值: 30000 最大值: 110000
    key="0.3.85",
    name="pressure",  # 大气气压
    device_class=SensorDeviceClass.PRESSURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=PRESSURE_KPA,
    scale=0.001,
    precision=2,
)

illuminance_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 83000 步长: 单位:
    key="0.3.85",
    name="illuminance",  # 光照度
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=LIGHT_LUX,
    scale=1,
    precision=0,
)

tvoc_desc = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 83000 步长: 单位:
    key="0.3.85",
    name="TVOC",  # 总挥发性有机物
    device_class=SensorDeviceClass.GAS,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    scale=1,
    precision=0,
)

# vibration
vibration_desc = AqaraSensorEntityDescription(
    key="0.3.85",
    name="vibration",
)

common_desp = AqaraSensorEntityDescription(
    key="0.3.85",
    name="common",
)

cube_status_desp = AqaraSensorEntityDescription(  # 最小值: 0 最大值: 100 步长: 单位: ,cube_status
    # rotate: rotate,move: move,swing: swing,flip90: flip90,alert: alert,shake_air: shake_air,
    # tap_twice: tap_twice,shake_in_plane: shake_in_plane,flip180: flip180
    # 1、flip90-翻转90° ,
    # 2、flip180-翻转180°
    # 3、move-轻推
    # 4、tap_twice-敲击两下
    # 5、shake_in_plane-扔一扔（实际没用上）
    # 6、shake_air-摇一摇
    # 7、swing-甩一下
    # 8、rotate-旋转（实际上不使用，直接使用度数）
    # 9、alert-静止一分钟后被触动
    # 10，rotate_degree——旋转
    # 28: 拿起保持
    # 20: 静止一分钟被触发
    # 29: 甩一甩
    # 16: 平面旋转
    # 0: 翻转90°
    # 1: 翻转180°
    # 17: 敲击两下
    # 3: 摇一摇
    # 2: 轻推
    key="13.1.85",
    name="魔方状态",
)
cube_rotate_degree_desp = AqaraSensorEntityDescription(  # rotate_degree  # 最小值: -100 最大值: 100 步长: 单位:
    # 上报的数据是角度对应的百分比，单位1%，取值为实际角度值除以360
    key="0.3.85",
    name="Rotating degree",  # 旋转度数
    device_class=SensorDeviceClass.AQI,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=EMPTY_UNIT,
    scale=1,
    precision=0,
)
cube_rotate_side = AqaraSensorEntityDescription(  # rotate_degree  # 最小值: -100 最大值: 100 步长: 单位:
    # 上面旋转时的朝上面 1: 第2面  0: 第1面 3: 第4面  2: 第3面 5: 第6面 4: 第5面
    key="13.101.85",
    name="action surface",  # 动作面
    device_class=SensorDeviceClass.AQI,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=EMPTY_UNIT,
    scale=1,
    precision=0,
)
cube_rotate_side_status = AqaraSensorEntityDescription(
    # 1: 第2面 0: 第1面 3: 第4面 2: 第3面 5: 第6面 4: 第5面
    key="13.103.85",
    name="Top surface",  # 当前朝上面
    device_class=SensorDeviceClass.AQI,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=EMPTY_UNIT,
    scale=1,
    precision=0,
)
common_cube = (  #
    cube_status_desp,
    cube_rotate_degree_desp,  # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
    *BATTERY_SENSORS,
)


switch_ch1_status_desc = AqaraSensorEntityDescription(
    key="13.1.85",
    name="button 1",
    icon="mdi:light-switch",
)

switch_ch2_status_desc = AqaraSensorEntityDescription(
    key="13.2.85",
    name="button 2",
    icon="mdi:light-switch",
)

switch_ch3_status_desc = AqaraSensorEntityDescription(  #
    key="13.3.85",
    name="button 3",
    icon="mdi:light-switch",
)

dual_switch_status_desc = AqaraSensorEntityDescription(  #
    key="13.3.85",
    name="button",
    icon="mdi:light-switch",
    native_unit_of_measurement=EMPTY_UNIT,
)


SENSORS: dict[str, tuple[AqaraSensorEntityDescription, ...]] = {
    "lumi.sensor_ht.jcn001": (  # 京鱼座温湿度传感器L版
        temp_desc,
        humidity_desc,
        air_pressure_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_ht.agl03": (  # 土壤温湿度传感器
        temp_desc.set_key("0.1.85").set_name("温度"),
        humidity_desc.set_key("0.2.85").set_name("湿度"),
        temp_desc.set_key("0.3.85").set_name("通道3的温度"),
        temp_desc.set_key("0.4.85").set_name("通道4的温度"),
        temp_desc.set_key("0.5.85").set_name("通道5的温度"),
        temp_desc.set_key("0.6.85").set_name("通道6的温度"),
        temp_desc.set_key("0.7.85").set_name("通道7的温度"),
        temp_desc.set_key("0.8.85").set_name("通道8的温度"),
        temp_desc.set_key("0.9.85").set_name("通道9的温度"),
        temp_desc.set_key("0.10.85").set_name("通道10的温度"),
        humidity_desc.set_key("0.11.85").set_name("通道1的湿度"),
        humidity_desc.set_key("0.12.85").set_name("通道2的湿度"),
        humidity_desc.set_key("0.13.85").set_name("通道3的湿度"),
        humidity_desc.set_key("0.14.85").set_name("通道4的湿度"),
        humidity_desc.set_key("0.15.85").set_name("通道5的湿度"),
        humidity_desc.set_key("0.16.85").set_name("通道6的湿度"),
        humidity_desc.set_key("0.17.85").set_name("通道7的湿度"),
        humidity_desc.set_key("0.18.85").set_name("通道8的湿度"),
        humidity_desc.set_key("0.19.85").set_name("通道9的湿度"),
        humidity_desc.set_key("0.20.85").set_name("通道10的湿度"),
        *BATTERY_SENSORS,
    ),
    "lumi.sen_ill.eicn01": (
        illuminance_desc,
        *BATTERY_SENSORS,
    ),  # 光照传感器 J1
    "aqara.adetector.drcn01": (  # 造梦者空气贝贝二代
        temp_desc.set_key("0.1.85").set_name("温度"),
        humidity_desc.set_key("0.2.85").set_name("湿度"),
        co2_desc.set_key("0.6.85").set_name("室内CO2"),
        co2_desc.set_key("0.19.85").set_name("所在城市室外PM2.5"),
        pm25_desc.set_key("0.19.85").set_name("所在城市室外PM2.5"),
        pm25_desc.set_key("0.20.85").set_name("室内PM2.5"),
        pm25_evaluate_desc.set_key("13.12.85").set_name("室内PM2.5评价"),
        pm25_desc.set_key("13.8.85").set_name("室内CO2评价"),
        *BATTERY_SENSORS,
    ),
    "lumi.airmonitor.acn01": (  # TVOC空气健康伴侣
        temp_desc.set_key("0.1.85").set_name("温度"),
        humidity_desc.set_key("0.2.85").set_name("湿度"),
        tvoc_desc.set_key("0.3.85").set_name("总挥发性有机物"),
        common_desp.set_key("13.1.85").set_name("TVOC等级"),
        *BATTERY_SENSORS,
    ),
    "lumi.plantmonitor.agl01": (  # 土壤PH值传感器
        common_desp.set_key("0.1.85").set_name("通道1的酸碱度"),
        common_desp.set_key("0.2.85").set_name("通道2的酸碱度"),
        common_desp.set_key("0.3.85").set_name("通道3的酸碱度"),
        common_desp.set_key("0.4.85").set_name("通道4的酸碱度"),
        common_desp.set_key("0.5.85").set_name("通道5的酸碱度"),
        common_desp.set_key("0.6.85").set_name("通道6的酸碱度"),
        common_desp.set_key("0.7.85").set_name("通道7的酸碱度"),
        common_desp.set_key("0.8.85").set_name("通道8的酸碱度"),
        common_desp.set_key("0.9.85").set_name("通道9的酸碱度"),
        common_desp.set_key("0.10.85").set_name("通道10的酸碱度"),
        *BATTERY_SENSORS,
    ),
    "lumi.airmonitor.agl02": (  # 二氧化碳传感器  最小值: 0 最大值: 5000  步长: 单位:
        co2_desc.set_key("0.1.85").set_name("通道1的二氧化碳浓度"),
        co2_desc.set_key("0.2.85").set_name("通道2的二氧化碳浓度"),
        co2_desc.set_key("0.3.85").set_name("通道3的二氧化碳浓度"),
        co2_desc.set_key("0.4.85").set_name("通道4的二氧化碳浓度"),
        co2_desc.set_key("0.5.85").set_name("通道5的二氧化碳浓度"),
        co2_desc.set_key("0.6.85").set_name("通道6的二氧化碳浓度"),
        co2_desc.set_key("0.7.85").set_name("通道7的二氧化碳浓度"),
        co2_desc.set_key("0.8.85").set_name("通道8的二氧化碳浓度"),
        co2_desc.set_key("0.9.85").set_name("通道9的二氧化碳浓度"),
        co2_desc.set_key("0.10.85").set_name("通道10的二氧化碳浓度"),
        *BATTERY_SENSORS,
    ),
    "miot.airmonitor.b1": (  # 小米米家空气检测仪  最小值: 0 最大值: 5000  步长: 单位:
        pm25_desc.set_key("13.1.85").set_name("PM2.5 Density"),
        humidity_desc.set_key("13.3.85").set_name("Environment Relative Humidity"),
        temp_desc.set_key("13.4.85").set_name("Environment Temperature"),
        co2_desc.set_key("13.5.85").set_name("Environment CO2 Density"),
        tvoc_desc.set_key("13.6.85").set_name("Environment TVOC Density"),
        *BATTERY_SENSORS,
    ),
    "miot.airmonitor.v1": (  # 米家PM2.5(zhimi.airmonitor.v1)
        pm25_desc.set_key("13.1.85").set_name("PM2.5 Density"),
        *BATTERY_SENSORS,
    ),
    "lumi.airm.fhac01": (  # 空气监测面板S1
        temp_desc.set_key("0.1.85").set_name("当前温度"),
        humidity_desc.set_key("0.2.85").set_name("湿度"),
        co2_desc.set_key("0.6.85").set_name("CO2浓度"),
        pm25_desc.set_key("0.19.85").set_name("PM2.5浓度"),
        common_desp.set_key("13.11.85").set_name("CO2浓度等级"),
        common_desp.set_key("13.12.85").set_name("PM2.5浓度等级"),
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_gas.acn001": (  # Aqara天然气报警器 X1
        temp_desc.set_key("0.1.85").set_name("当前温度"),
        tvoc_desc.set_key("0.5.85").set_name(
            "当前天然气浓度"
        ),  # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_gas.jcn001": (  # 京鱼座天然气报警器L版
        temp_desc.set_key("0.1.85").set_name("当前温度"),
        tvoc_desc.set_key("0.5.85").set_name(
            "当前天然气浓度"
        ),  # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        *BATTERY_SENSORS,
    ),
    "lumi.sen_gas.hrcn01": (  # 无线燃气表
        temp_desc.set_key("0.1.85").set_name("当前温度"),
        tvoc_desc.set_key("0.5.85").set_name("燃气表值"),  # 最小值: 0 最大值: 4294967295 步长: 单位
        common_desp.set_key("14.1.85").set_name("燃气表阀门状态"),  # 燃气表阀门状态： 1: 开 2: 强制关
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_gas.acn02": (  # Aqara天然气报警器
        temp_desc.set_key("0.1.85").set_name("当前温度"),
        tvoc_desc.set_key("0.5.85").set_name(
            "当前天然气浓度"
        ),  # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        common_desp.set_key("14.1.85").set_name("燃气表阀门状态"),  # 燃气表阀门状态： 1: 开 2: 强制关
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_natgas.v1": (  # 天然气传感器 # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        tvoc_desc.set_key("0.1.85").set_name("天然气浓度上报"),
        common_desp.set_key("14.1.85").set_name("燃气表阀门状态"),  # 燃气表阀门状态： 1: 开 2: 强制关
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_smoke.acn05": (  # Aqara烟雾报警器 X1 # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        tvoc_desc.set_key("0.5.85").set_name("当前烟雾浓度"),
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_smoke.jcn01": (  # 京鱼座烟雾报警器L版 # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        tvoc_desc.set_key("0.5.85").set_name("当前烟雾浓度"),
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_smoke.acn03": (  # Aqara烟雾报警器 # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        tvoc_desc.set_key("0.5.85").set_name("当前烟雾浓度"),
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_smoke.acn02": (  # 烟雾传感器
        common_desp.set_key("0.1.85").set_name(
            "density"
        ),  # 最小值: 0 最大值: 5 步长: 单位: OBS%/F
        common_desp.set_key("14.1.111").set_name("报警状态"),
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_smoke.v1": (  # 烟雾传感器
        common_desp.set_key("0.1.85").set_name(
            "density"
        ),  # 最小值: 0 最大值: 5 步长: 单位: OBS%/F
        common_desp.set_key("14.1.111").set_name("报警状态"),  # 报警状态，0:没报警，
        *BATTERY_SENSORS,
    ),
    "aqara.sensor_smoke.eicn01": (  # 独立式光电感烟火灾探测报警器
        common_desp.set_key("13.1.85").set_name("报警状态"),  # 报警状态，0:没报警，
        *BATTERY_SENSORS,
    ),
    # cube###################
    "lumi.remote.cagl02": (  # 魔方控制器 T1 Pro
        cube_status_desp,
        cube_rotate_degree_desp.set_key("0.21.85"),  # 最小值: 0 最大值: 100 步长: 1 单位: %LEL
        cube_rotate_side,
        cube_rotate_side_status,
        *BATTERY_SENSORS,
    ),
    # ########################################################
    "aqara.tow_w.acn001": (temp_desc.set_key("0.1.85").set_name("当前温度"),),
    # ####################lock################################
    "lumi.vibration.aq1": (
        common_desp.set_key("13.1.85").set_name("vibration"),
        *BATTERY_SENSORS,
    ),
    "lumi.vibration.agl01": (
        common_desp.set_key("13.7.85").set_name("vibration"),
        *BATTERY_SENSORS,
    ),
    # wireless switch######################
    "lumi.remote.acn009": (  # Aqara无线开关 H1M（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        dual_switch_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.acn008": (  # Aqara无线开关 H1M（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.jcn002": (  # 京鱼座无线开关L版
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.acn007": (  # 无线开关 E1
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.acn003": (  # 无线开关 E1（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.acn004": (  # 无线开关 E1（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        dual_switch_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.acn002": (  # Aqara无线开关 X1（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        dual_switch_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.acn001": (  # Aqara无线开关 X1（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.rkba01": (  # 智能旋钮开关 H1（无线版）
        switch_ch1_status_desc,
        cube_rotate_side.set_key("0.21.85").set_name("current rotate angle"),
        cube_rotate_side.set_key("0.22.85").set_name("sum rotate angle"),
        cube_rotate_side.set_key("0.23.85").set_name("current rotate angle percent"),
        cube_rotate_side.set_key("0.24.85").set_name("sum rotate angle percent"),
        cube_rotate_side.set_key("0.25.85").set_name("rotate_cumulate_time"),
        cube_rotate_side.set_key("0.26.85").set_name("press_current_rotate_angle"),
        cube_rotate_side.set_key("0.27.85").set_name("press_sum_rotate_angle"),
        cube_rotate_side.set_key("0.28.85").set_name("press_cur_rotate_angle_per"),
        cube_rotate_side.set_key("0.29.85").set_name("press_sum_rotate_angle_percent"),
        cube_rotate_side.set_key("0.20.85").set_name("spress_rotate_cumulate_time"),
        *BATTERY_SENSORS,
    ),
    "lumi.switch.n6eic2": (  # 爱根斯通场景开关6路
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        switch_ch3_status_desc,
        switch_ch1_status_desc.set_key("13.4.85").set_name("button 4"),
        switch_ch2_status_desc.set_key("13.6.85").set_name(
            "button 5"
        ),  # key is 13.6.85 not 13.5.85
        switch_ch3_status_desc.set_key("13.7.85").set_name(
            "button 6"
        ),  # key is 13.7.85
        *BATTERY_SENSORS,
    ),
    "lumi.switch.n4eic2": (  # 爱根斯通场景开关4路
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        switch_ch3_status_desc,
        switch_ch1_status_desc.set_key("13.4.85").set_name("button 4"),
        *BATTERY_SENSORS,
    ),
    "lumi.switch.n3eic2": (  # 爱根斯通场景开关3路
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        switch_ch3_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.switch.n2eic2": (  # 爱根斯通场景开关2路
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.switch.n1eic2": (  # 爱根斯通场景开关2路
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b1akr1": (  # 无线开关 D1 贴墙式双键版
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b286acn03": (  # 无线开关 T1（贴墙式双键）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b686opcn01": (  # 无线场景开关（六键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        switch_ch3_status_desc,
        switch_ch1_status_desc.set_key("13.4.85").set_name("button 4"),
        switch_ch2_status_desc.set_key("13.6.85").set_name(
            "button 5"
        ),  # key is 13.6.85 not 13.5.85
        switch_ch3_status_desc.set_key("13.7.85").set_name(
            "button 6"
        ),  # key is 13.7.85
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b486opcn01": (  # 无线场景开关（四键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        switch_ch3_status_desc,
        switch_ch1_status_desc.set_key("13.4.85").set_name("button 4"),
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b286opcn01": (  # 无线场景开关（双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b186acn03": (  # 无线开关 T1（贴墙式单键）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b1acn02": (  # 无线开关T1
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_switch.aq3": (  # 无线开关（升级版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_switch.v1": (  # 无线开关
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_switch.es3": (  # 无线开关（升级版
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_switch.es2": (  # 无线开关
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_switch.v2": (  # 无线开关
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_switch.aq2": (  # 无线开关
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_86sw2.v1": (  # 无线开关（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_86sw2.es1": (  # 无线开关（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b1acn01": (  # 无线开关
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_86sw1.es1": (  # 无线开关（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b186acn01": (  # 无线开关（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_86sw1.aq1": (  # 无线开关（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_86sw2.aq1": (  # 无线开关（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b286acn01": (  # 无线开关（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.sensor_86sw1.v1": (  # 无线开关（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b28ac1": (  # 无线开关 H1（贴墙式双键版）
        switch_ch1_status_desc,
        switch_ch2_status_desc,
        *BATTERY_SENSORS,
    ),
    "lumi.remote.b18ac1": (  # 线开关 H1（贴墙式单键版）
        switch_ch1_status_desc,
        *BATTERY_SENSORS,
    ),
}

common_temp_sensor = SENSORS["lumi.sensor_ht.jcn001"]

# 温湿度传感器
SENSORS["lumi.sensor_ht.agl02"] = common_temp_sensor
SENSORS["lumi.weather.es1"] = common_temp_sensor
SENSORS["lumi.weather.v1"] = common_temp_sensor
SENSORS["lumi.sensor_ht.v1"] = common_temp_sensor
SENSORS["lumi.sensor_ht.es1"] = common_temp_sensor

# 照度传感器
common_illumination_sensor = SENSORS["lumi.sen_ill.eicn01"]
SENSORS["lumi.sen_ill.akr01"] = common_illumination_sensor
SENSORS["lumi.sen_ill.mgl01"] = common_illumination_sensor
SENSORS["lumi.sen_ill.agl01"] = common_illumination_sensor

# 魔方传感器
# 京鱼座魔方控制器L版
SENSORS["lumi.remote.jcn001"] = common_cube
# 魔方控制器 J1
SENSORS["lumi.remote.eicn01"] = common_cube

# Aqara魔方控制器T1
SENSORS["lumi.remote.cagl01"] = common_cube
# 魔方控制器
SENSORS["lumi.sensor_cube.aqgl01"] = common_cube
# 魔方控制器
SENSORS["lumi.sensor_cube.es1"] = common_cube
# 魔方控制器
SENSORS["lumi.sensor_cube.v1"] = common_cube


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara sensor dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara sensor."""
        entities: list[AqaraSensorEntity] = []

        def append_entity(aqara_point, description):

            entity: AqaraSensorEntity = AqaraSensorEntity(
                aqara_point, hass_data.device_manager, description
            )
            entities.append(entity)

            async_dispatcher_connect(
                hass,
                f"{AQARA_HA_SIGNAL_UPDATE_POINT_VALUE}_{string_dot_to_underline(aqara_point.id)}",
                entity.async_update_attr,
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, SENSORS, append_entity
        )
        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraSensorEntity(AqaraEntity, SensorEntity):
    """Aqara Sensor Entity."""

    entity_description: AqaraSensorEntityDescription

    _value_range: DeviceValueRange | None = None
    _type_data: IntegerTypeData | EnumTypeData | None = None
    _uom: UnitOfMeasurement | None = None

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraSensorEntityDescription,
    ) -> None:
        """Init Aqara sensor."""
        super().__init__(point, device_manager)
        self.entity_description = description

    async def async_update_attr(self, point: AqaraPoint) -> None:

        model = self.device_info.get("model")

        modelInfo = aqara_events_map.get(str(model))
        if modelInfo is None:
            return

        resourceInfo = modelInfo.get(point.resource_id)
        if resourceInfo is None:
            return

        eventType = resourceInfo.get(point.value)

        if self.registry_entry is not None:
            device_id = self.registry_entry.device_id
        else:
            device_id = ""

        if eventType is not None:
            message = {
                "device_id": device_id,
                "type": eventType,
            }
            self.hass.bus.async_fire("aqara_event", message)

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        point_value = self.point.get_value()
        if point_value is None or point_value == "":
            return None
        value: float = 0
        try:
            if self.entity_description.scale is not None:
                value = float(point_value) * self.entity_description.scale
            else:
                value = float(point_value)
            if self.entity_description.precision is not None:
                if self.entity_description.precision == 0:
                    return round(value)
                else:
                    return round(value, self.entity_description.precision)
            else:
                return value
        except Exception:
            return point_value
