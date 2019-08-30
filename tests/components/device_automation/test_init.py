"""The test for light device automation."""
import pytest

from homeassistant.setup import async_setup_component
from homeassistant.components.websocket_api.const import TYPE_RESULT
from homeassistant.helpers import device_registry


from tests.common import MockConfigEntry, mock_device_registry, mock_registry


@pytest.fixture
def device_reg(hass):
    """Return an empty, loaded, registry."""
    return mock_device_registry(hass)


@pytest.fixture
def entity_reg(hass):
    """Return an empty, loaded, registry."""
    return mock_registry(hass)


def _same_dicts(a, b):
    if len(a) != len(b):
        return False

    for d in a:
        if d not in b:
            return False
    return True


async def test_websocket_get_actions(hass, hass_ws_client, device_reg, entity_reg):
    """Test we get the expected conditions from a light through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create("light", "test", "5678", device_id=device_entry.id)
    expected_actions = [
        {
            "device": None,
            "domain": "light",
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": "light.test_5678",
        },
        {
            "device": None,
            "domain": "light",
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": "light.test_5678",
        },
    ]

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/list_actions",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    actions = msg["result"]["actions"]
    assert _same_dicts(actions, expected_actions)


async def test_websocket_get_conditions(hass, hass_ws_client, device_reg, entity_reg):
    """Test we get the expected conditions from a light through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create("light", "test", "5678", device_id=device_entry.id)
    expected_conditions = [
        {
            "condition": "device",
            "domain": "light",
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": "light.test_5678",
        },
        {
            "condition": "device",
            "domain": "light",
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": "light.test_5678",
        },
    ]

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/list_conditions",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    conditions = msg["result"]["conditions"]
    assert _same_dicts(conditions, expected_conditions)


async def test_websocket_get_triggers(hass, hass_ws_client, device_reg, entity_reg):
    """Test we get the expected triggers from a light through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create("light", "test", "5678", device_id=device_entry.id)
    expected_triggers = [
        {
            "platform": "device",
            "domain": "light",
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": "light.test_5678",
        },
        {
            "platform": "device",
            "domain": "light",
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": "light.test_5678",
        },
    ]

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/list_triggers",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    triggers = msg["result"]["triggers"]
    assert _same_triggers(triggers, expected_triggers)
