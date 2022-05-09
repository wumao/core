"""Test the Aqara config flow."""
# from __future__ import annotations
from unittest.mock import MagicMock, patch
from homeassistant import config_entries, data_entry_flow
from homeassistant.components.aqara.const import (
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)

import pytest

from homeassistant.core import HomeAssistant

MOCK_COUNTRY = "China"
MOCK_USERNAME = "myUsername"
MOCK_PASSWORD = "myPassword"
COUNTRY_CODE = "86"

AQARA_INPUT_DATA = {
    CONF_COUNTRY_CODE: MOCK_COUNTRY,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
}


@pytest.fixture(name="aqara")
def aqara_fixture() -> MagicMock:
    """Patch libraries."""
    with patch("homeassistant.components.aqara.config_flow.AqaraOpenAPI") as aqara:
        yield aqara


@pytest.fixture(name="aqara_setup", autouse=True)
def aqara_setup_fixture() -> None:
    """Mock aqara entry setup."""
    with patch("homeassistant.components.aqara.async_setup_entry", return_value=True):
        yield


async def test_user_flow(
    hass: HomeAssistant,
    aqara: MagicMock,
):
    """Test user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    aqara().get_auth = MagicMock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=AQARA_INPUT_DATA
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == MOCK_USERNAME
    assert result["data"][CONF_USERNAME] == MOCK_USERNAME
    assert result["data"][CONF_PASSWORD] == MOCK_PASSWORD
    assert result["data"][CONF_COUNTRY_CODE] == COUNTRY_CODE
    assert not result["result"].unique_id


async def test_error_on_invalid_credentials(hass, aqara):
    """Test when we have invalid credentials."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    aqara().get_auth = MagicMock(return_value=False)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=AQARA_INPUT_DATA
    )
    await hass.async_block_till_done()

    assert result["errors"]["base"] == "login_error"
    assert result["description_placeholders"]["code"] == -1
    assert result["description_placeholders"]["msg"] == "error"
