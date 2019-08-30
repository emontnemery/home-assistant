"""Provides device automations for lights."""
import voluptuous as vol

import homeassistant.components.automation.state as state
from homeassistant.core import split_entity_id
from homeassistant.const import (
    CONF_CONDITION,
    CONF_DEVICE,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.helpers import condition, config_validation as cv, service
from homeassistant.helpers.entity_registry import async_entries_for_device
from . import DOMAIN


# mypy: allow-untyped-defs, no-check-untyped-defs

CONF_TURN_OFF = "turn_off"
CONF_TURN_ON = "turn_on"
CONF_TOGGLE = "toggle"

ENTITY_ACTIONS = [
    {
        # Turn light off
        CONF_DEVICE: None,
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TURN_OFF,
    },
    {
        # Turn light on
        CONF_DEVICE: None,
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TURN_ON,
    },
    {
        # Toggle light
        CONF_DEVICE: None,
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TOGGLE,
    },
]

ENTITY_CONDITIONS = [
    {
        # True when light is turned off
        CONF_CONDITION: "device",
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TURN_OFF,
    },
    {
        # True when light is turned on
        CONF_CONDITION: "device",
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TURN_ON,
    },
]

ENTITY_TRIGGERS = [
    {
        # Trigger when light is turned off
        CONF_PLATFORM: "device",
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TURN_OFF,
    },
    {
        # Trigger when light is turned on
        CONF_PLATFORM: "device",
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: CONF_TURN_ON,
    },
]

ACTION_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_DEVICE): None,
            vol.Optional(CONF_DEVICE_ID): str,
            vol.Required(CONF_DOMAIN): DOMAIN,
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In([CONF_TOGGLE, CONF_TURN_OFF, CONF_TURN_ON]),
        }
    )
)

CONDITION_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_CONDITION): "device",
            vol.Optional(CONF_DEVICE_ID): str,
            vol.Required(CONF_DOMAIN): DOMAIN,
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In([CONF_TURN_OFF, CONF_TURN_ON]),
        }
    )
)

TRIGGER_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_PLATFORM): "device",
            vol.Optional(CONF_DEVICE_ID): str,
            vol.Required(CONF_DOMAIN): DOMAIN,
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In([CONF_TURN_OFF, CONF_TURN_ON]),
        }
    )
)


def _is_domain(entity, domain):
    return split_entity_id(entity.entity_id)[0] == domain


async def async_action_from_config(hass, config, variables, context):
    """Change state based on configuration."""
    config = ACTION_SCHEMA(config)
    action_type = config[CONF_TYPE]
    if action_type == CONF_TURN_ON:
        action = "turn_on"
    elif action_type == CONF_TURN_OFF:
        action = "turn_off"
    else:
        action = "toggle"
    service_action = {
        service.CONF_SERVICE: "light.{}".format(action),
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
    }

    await service.async_call_from_config(
        hass,
        service_action,
        blocking=True,
        variables=variables,
        # validate_config=False,
        context=context,
    )


def async_condition_from_config(config, config_validation):
    """Evaluate state based on configuration."""
    config = CONDITION_SCHEMA(config)
    condition_type = config[CONF_TYPE]
    if condition_type == CONF_TURN_ON:
        stat = "on"
    else:
        stat = "off"
    state_config = {
        condition.CONF_CONDITION: "state",
        condition.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        condition.CONF_STATE: stat,
    }

    return condition.state_from_config(state_config, config_validation)


async def async_attach_trigger(hass, config, action, automation_info):
    """Listen for state changes based on configuration."""
    config = TRIGGER_SCHEMA(config)
    trigger_type = config[CONF_TYPE]
    if trigger_type == CONF_TURN_ON:
        from_state = "off"
        to_state = "on"
    else:
        from_state = "on"
        to_state = "off"
    state_config = {
        state.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state.CONF_FROM: from_state,
        state.CONF_TO: to_state,
    }

    return await state.async_trigger(hass, state_config, action, automation_info)


async def async_trigger(hass, config, action, automation_info):
    """Temporary so existing automation framework can be used for testing."""
    return await async_attach_trigger(hass, config, action, automation_info)


async def _async_get_automations(hass, device_id, automation_templates):
    """List device automations."""
    automations = []
    entity_registry = await hass.helpers.entity_registry.async_get_registry()

    entities = async_entries_for_device(entity_registry, device_id)
    domain_entities = [x for x in entities if _is_domain(x, DOMAIN)]
    for entity in domain_entities:
        for automation in automation_templates:
            automation = dict(automation)
            automation.update(device_id=device_id, entity_id=entity.entity_id)
            automations.append(automation)

    return automations


async def async_get_actions(hass, device_id):
    """List device actions."""
    return await _async_get_automations(hass, device_id, ENTITY_ACTIONS)


async def async_get_conditions(hass, device_id):
    """List device conditions."""
    return await _async_get_automations(hass, device_id, ENTITY_CONDITIONS)


async def async_get_triggers(hass, device_id):
    """List device triggers."""
    return await _async_get_automations(hass, device_id, ENTITY_TRIGGERS)
