"""Provides device automations for Cover."""
from typing import Any, Dict, List
import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    CONF_ABOVE,
    CONF_BELOW,
    CONF_CONDITION,
    CONF_DOMAIN,
    CONF_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITY_ID,
    STATE_OPEN,
    STATE_CLOSED,
    STATE_OPENING,
    STATE_CLOSING,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    condition,
    config_validation as cv,
    entity_registry,
    template,
)
from homeassistant.helpers.typing import ConfigType, TemplateVarsType
from homeassistant.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from . import (
    DOMAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
)

POSTION_CONDITION_TYPES = {"is_position", "is_tilt_position"}
STATE_CONDITION_TYPES = {"is_open", "is_closed", "is_opening", "is_closing"}

POSITION_CONDITION_SCHEMA = vol.All(
    DEVICE_CONDITION_BASE_SCHEMA.extend(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In(STATE_CONDITION_TYPES),
        }
    ),
    cv.has_at_least_one_key(CONF_BELOW, CONF_ABOVE),
)

STATE_CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(POSTION_CONDITION_TYPES),
    }
)

CONDITION_SCHEMA = vol.Any(POSITION_CONDITION_SCHEMA, STATE_CONDITION_SCHEMA)


async def async_get_conditions(hass: HomeAssistant, device_id: str) -> List[dict]:
    """List device conditions for Cover devices."""
    registry = await entity_registry.async_get_registry(hass)
    conditions: List[Dict[str, Any]] = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = hass.states.get(entry.entity_id)
        if not state or ATTR_SUPPORTED_FEATURES not in state.attributes:
            continue

        supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
        supports_open_close = supported_features & (SUPPORT_OPEN | SUPPORT_CLOSE)

        # Add conditions for each entity that belongs to this integration
        if supports_open_close:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_open",
                }
            )
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_closed",
                }
            )
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_opening",
                }
            )
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_closing",
                }
            )
        if supported_features & SUPPORT_SET_POSITION:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_position",
                }
            )
        if supported_features & SUPPORT_SET_TILT_POSITION:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_tilt_position",
                }
            )

    return conditions


async def async_get_condition_capabilities(hass: HomeAssistant, config: dict) -> dict:
    """List condition capabilities."""
    if config[CONF_TYPE] not in ["is_position", "is_tilt_position"]:
        return {}

    return {
        "extra_fields": vol.Schema(
            {
                vol.Optional(CONF_ABOVE): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=100)
                ),
                vol.Optional(CONF_BELOW): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=100)
                ),
            }
        )
    }


def async_condition_from_config(
    config: ConfigType, config_validation: bool
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config_validation:
        config = CONDITION_SCHEMA(config)

    if config[CONF_TYPE] in STATE_CONDITION_TYPES:
        if config[CONF_TYPE] == "is_open":
            state = STATE_OPEN
        elif config[CONF_TYPE] == "is_closed":
            state = STATE_CLOSED
        elif config[CONF_TYPE] == "is_opening":
            state = STATE_OPENING
        elif config[CONF_TYPE] == "is_closing":
            state = STATE_CLOSING

        def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
            """Test if an entity is a certain state."""
            return condition.state(hass, config[ATTR_ENTITY_ID], state)

        return test_is_state

    if config[CONF_TYPE] == "is_position":
        position = "current_cover_position"
    if config[CONF_TYPE] == "is_tilt_position":
        position = "current_cover_tilt_position"
    min_pos = config.get(CONF_ABOVE, -1)
    max_pos = config.get(CONF_BELOW, 101)
    value_template = template.Template(  # type: ignore
        f"{{ (state_attr('{config[ATTR_ENTITY_ID]}', '{position}')|int) > {min_pos} and (state_attr('{config[ATTR_ENTITY_ID]}', '{position}')|int) < {max_pos} }}"
    )

    def template_if(hass: HomeAssistant, variables: TemplateVarsType = None) -> bool:
        """Validate template based if-condition."""
        value_template.hass = hass

        return condition.async_template(hass, value_template, variables)

    return template_if
