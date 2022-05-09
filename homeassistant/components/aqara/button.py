"""Support for Aqara buttons."""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from aqara_iot import AqaraPoint, AqaraDeviceManager

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
    # ButtonDeviceClass,
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
class AqaraButtonEntityDescription(ButtonEntityDescription):
    """Describes a Aqara button sensor."""

    # Value to consider button to be "pressed"
    press_value: bool | float | int | str = True


# All descriptions can be found here.
BUTTONS: dict[str, tuple[AqaraButtonEntityDescription, ...]] = {
    "aqara.bed.hhcn03": (  # 智能电动床W1
        AqaraButtonEntityDescription(  # 停止
            key="4.7.85",  # switch_nostatus
            name="停止",
            icon="mdi:stop",
            entity_category=EntityCategory.CONFIG,
            press_value=1,
        ),
        AqaraButtonEntityDescription(  # 停止
            key="14.1.85",  # switch_nostatus
            name="start",
            icon="mdi:stop",
            entity_category=EntityCategory.CONFIG,
            press_value=1,
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqara buttons dynamically through Aqara discovery."""
    hass_data: HomeAssistantAqaraData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Aqara buttons."""
        entities: list[AqaraButtonEntity] = []

        def append_entity(aqara_point, description: AqaraButtonEntityDescription):
            entities.append(
                AqaraButtonEntity(aqara_point, hass_data.device_manager, description)
            )

        find_aqara_device_points_and_register(
            hass, entry.entry_id, hass_data, device_ids, BUTTONS, append_entity
        )

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, AQARA_DISCOVERY_NEW, async_discover_device)
    )


class AqaraButtonEntity(AqaraEntity, ButtonEntity):
    """Aqara Button Device."""

    entity_description: AqaraButtonEntityDescription

    def __init__(
        self,
        point: AqaraPoint,
        device_manager: AqaraDeviceManager,
        description: AqaraButtonEntityDescription,
    ) -> None:
        """Init Aqara button."""
        super().__init__(point, device_manager)
        self.entity_description = description

    def press(self, **kwargs: Any) -> None:
        """Press the button."""
        self._send_command(
            {self.point.resource_id: self.entity_description.press_value}
        )
