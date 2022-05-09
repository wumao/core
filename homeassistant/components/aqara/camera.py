"""Support for Aqara cameras."""
from __future__ import annotations
from dataclasses import dataclass

from aqara_iot import AqaraPoint, AqaraDeviceManager

# from homeassistant.components import ffmpeg
from homeassistant.components.camera import (
    SUPPORT_STREAM,
    Camera as CameraEntity,
    CameraEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeAssistantAqaraData
from .base import AqaraEntity, find_aqara_device_points_and_register

from .const import DOMAIN, AQARA_DISCOVERY_NEW

from homeassistant.components.camera.const import StreamType


@dataclass
class AqaraCameraEntityDescription(CameraEntityDescription):
    """Describes a Aqara Camera entity."""


# All descriptions can be found here.
CAMERAS: dict[str, tuple[AqaraCameraEntityDescription, ...]] = {
    "lumi.camera.agl001": (  # 智能摄像机G2H Pro(海外版)
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.acn003": (  # 智能摄像机G2H Pro
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.akr001": (  # LGU-G3
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="14.74.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.gwpgl1": (  # 智能摄像机G3（海外版）
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.gwpagl01": (  # 智能摄像机G3
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="14.74.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.gwag03": (  # 智能摄像机 G2H（海外版）
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.gwakr1": (  # 智能摄像机 G2H（海外版）
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.gwagl02": (  # 智能摄像机 G2H（海外版）
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
    "lumi.camera.gwagl01": (  # 智能摄像机 G2H（海外版）
        AqaraCameraEntityDescription(  # 0: 关闭 1: 打开 255: 常开
            key="4.8.85",
            name="开关摄像头",
            icon="mdi:restart",
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara cameras dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara camera."""
        entities: list[AqaraCameraEntity] = []

        def append_entity(aqara_point, description):
            entities.append(
                AqaraCameraEntity(aqara_point, hass_data.device_manager, description)
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, CAMERAS, append_entity
        )

        # for device_id in device_ids:
        #     device = hass_data.device_manager.device_map[device_id]
        #     if device.model in CAMERAS.keys():
        #         entities.append(AqaraCameraEntity())

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraCameraEntity(AqaraEntity, CameraEntity):
    """Aqara Camera Entity."""

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraCameraEntityDescription,
    ) -> None:
        """Init Aqara Camera."""
        super().__init__(point, device_manager)
        CameraEntity.__init__(self)
        self._attr_frontend_stream_type = StreamType.WEB_RTC

        # _attr_frame_interval: float = MIN_STREAM_INTERVAL
        # _attr_frontend_stream_type: str | None
        self._attr_is_on = True
        self._attr_is_streaming = True

        # self._attr_supported_features

    # _attr_is_recording: bool = False
    # _attr_is_streaming: bool = False
    # _attr_model: str | None = None
    # _attr_motion_detection_enabled: bool = False
    # _attr_should_poll: bool = False  # No need to poll cameras
    # _attr_state: None = None  # State is determined by is_on
    # _attr_supported_features: int = 0

    @property
    def frontend_stream_type(self) -> StreamType | None:
        return StreamType.WEB_RTC

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_STREAM  # | SUPPORT_ON_OFF

    @property
    def is_recording(self) -> bool:
        """Return true if the device is recording."""
        # find the record point. get the value.
        return False

    @property
    def brand(self) -> str | None:
        """Return the camera brand."""
        return "Aqara"

    @property
    def motion_detection_enabled(self) -> bool:
        """Return the camera motion detection status."""
        return False

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return None

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        # raise NotImplementedError()
        # stream_source = await self.stream_source()
        # if not stream_source:
        #     return None
        # return await ffmpeg.async_get_image(
        #     self.hass,
        #     stream_source,
        #     width=width,
        #     height=height,
        # )

    # async def async_camera_image(
    #     self, width: int | None = None, height: int | None = None
    # ) -> bytes | None:
    #     """Return a still image response from the camera."""

    #     return None

    # @property
    # def model(self) -> str | None:
    #     """Return the camera model."""
    #     return self.point.model()

    def enable_motion_detection(self) -> None:
        """Enable motion detection in the camera."""
        # self._send_command([{self.point.resource_id: "1"}])
        return None

    def disable_motion_detection(self) -> None:
        """Disable motion detection in camera."""
        # self._send_command([{self.point.resource_id: "1"}])
        return None

    async def async_handle_web_rtc_offer(self, offer_sdp: str) -> str | None:
        """Handle the WebRTC offer and return an answer.

        This is used by cameras with SUPPORT_STREAM and STREAM_TYPE_WEB_RTC.
        """
        # try:
        #     stream = await self.device_manager.generate_web_rtc_stream(offer_sdp)
        # except GoogleNestException as err:
        #     raise HomeAssistantError(f"Nest API error: {err}") from err
        # return stream.answer_sdp
        # return await self.hass.async_add_executor_job(
        #     self.device_manager.get_device_stream_allocate,
        #     self.device.id,
        #     "rtsp",
        # )
        # raise NotImplementedError()
        return None

    def turn_off(self) -> None:
        """Turn off camera."""
        return None

    def turn_on(self) -> None:
        """Turn off camera."""
        return None

    # def connect_to_camera(self):
    #     ack = self.device_manager.request_connect_to_camera(self.point.did)
    #     self.device_manager.answer_camera()
    #     return None
