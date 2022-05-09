"""Tests for the Aqara sensor device."""
from unittest.mock import patch

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from .common import setup_platform

# from  aqara_iot import AqaraOpenMq
import aqara_iot.openmq
from .common import mock_start

DEVICE_ID = "sensor.shi_du_lumi_4cf8cdf3c7f7a25"
DEVICE_UID = "Aqara.lumi.4cf8cdf3c7f7a25__0.2.85"


async def test_entity_registry(hass: HomeAssistant) -> None:
    """Tests that the devices are registered in the entity registry."""
    # ("aqara_iot.AqaraOpenMQ.start") as mock_mq_start:
    with patch.object(aqara_iot.openmq.AqaraOpenMQ, "start", mock_start):
        await setup_platform(hass, SENSOR_DOMAIN)
        entity_registry = er.async_get(hass)

        entry = entity_registry.async_get(DEVICE_ID)
        print(entry)
        assert entry.unique_id == DEVICE_UID  # type: ignore[union-attr]


async def test_attributes(hass: HomeAssistant) -> None:
    """Test the sensor attributes are correct."""
    # with patch("aqara_iot.AqaraOpenMQ.start") as mock_mq_start:
    with patch.object(aqara_iot.openmq.AqaraOpenMQ, "start", mock_start):
        await setup_platform(hass, SENSOR_DOMAIN)

        state = hass.states.get(DEVICE_ID)
        print("===========================================")
        print(state)
        assert state.state == "78.2"  # type: ignore[union-attr]
        assert state.attributes.get("unit_of_measurement") == "%"  # type: ignore[union-attr]
        assert state.attributes.get("state_class") == "measurement"  # type: ignore[union-attr]
        assert state.attributes.get("device_class") == "temperature"  # type: ignore[union-attr]
