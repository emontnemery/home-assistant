"""The tests for the sun automation."""
from datetime import datetime

import pytest
from unittest.mock import patch

from homeassistant.setup import async_setup_component
from homeassistant.components import sun
import homeassistant.components.automation as automation
import homeassistant.util.dt as dt_util

from tests.common import (
    async_fire_time_changed, mock_component, async_mock_service)
from tests.components.automation import common


@pytest.fixture
def calls(hass):
    """Track calls to a mock serivce."""
    return async_mock_service(hass, 'test', 'automation')


@pytest.fixture(autouse=True)
def setup_comp(hass):
    """Initialize components."""
    mock_component(hass, 'group')
    dt_util.set_default_time_zone(hass.config.time_zone)
    hass.loop.run_until_complete(async_setup_component(hass, sun.DOMAIN, {
            sun.DOMAIN: {sun.CONF_ELEVATION: 0}}))


async def test_sunset_trigger(hass, calls):
    """Test the sunset trigger."""
    now = datetime(2015, 9, 15, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 2, tzinfo=dt_util.UTC)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        await async_setup_component(hass, automation.DOMAIN, {
            automation.DOMAIN: {
                'trigger': {
                    'platform': 'sun',
                    'event': 'sunset',
                },
                'action': {
                    'service': 'test.automation',
                }
            }
        })

    await common.async_turn_off(hass)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_time)
    await hass.async_block_till_done()
    assert 0 == len(calls)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        await common.async_turn_on(hass)
        await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_time)
    await hass.async_block_till_done()
    assert 1 == len(calls)


async def test_sunrise_trigger(hass, calls):
    """Test the sunrise trigger."""
    now = datetime(2015, 9, 13, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 14, tzinfo=dt_util.UTC)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        await async_setup_component(hass, automation.DOMAIN, {
            automation.DOMAIN: {
                'trigger': {
                    'platform': 'sun',
                    'event': 'sunrise',
                },
                'action': {
                    'service': 'test.automation',
                }
            }
        })

    async_fire_time_changed(hass, trigger_time)
    await hass.async_block_till_done()
    assert 1 == len(calls)


async def test_sunset_trigger_with_offset(hass, calls):
    """Test the sunset trigger with offset."""
    now = datetime(2015, 9, 15, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 2, 30, tzinfo=dt_util.UTC)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        await async_setup_component(hass, automation.DOMAIN, {
            automation.DOMAIN: {
                'trigger': {
                    'platform': 'sun',
                    'event': 'sunset',
                    'offset': '0:30:00'
                },
                'action': {
                    'service': 'test.automation',
                    'data_template': {
                        'some':
                        '{{ trigger.%s }}' % '}} - {{ trigger.'.join((
                            'platform', 'event', 'offset'))
                    },
                }
            }
        })

    async_fire_time_changed(hass, trigger_time)
    await hass.async_block_till_done()
    assert 1 == len(calls)
    assert 'sun - sunset - 0:30:00' == calls[0].data['some']


async def test_sunrise_trigger_with_offset(hass, calls):
    """Test the sunrise trigger with offset."""
    now = datetime(2015, 9, 13, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 13, 30, tzinfo=dt_util.UTC)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        await async_setup_component(hass, automation.DOMAIN, {
            automation.DOMAIN: {
                'trigger': {
                    'platform': 'sun',
                    'event': 'sunrise',
                    'offset': '-0:30:00'
                },
                'action': {
                    'service': 'test.automation',
                }
            }
        })

    async_fire_time_changed(hass, trigger_time)
    await hass.async_block_till_done()
    assert 1 == len(calls)


async def test_if_action_before(hass, calls):
    """Test if action was before."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'before': 'sunrise',
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    now = datetime(2015, 9, 16, 15, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    now = datetime(2015, 9, 16, 10, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)


async def test_if_action_after(hass, calls):
    """Test if action was after."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'after': 'sunrise',
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    now = datetime(2015, 9, 16, 13, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    now = datetime(2015, 9, 16, 15, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)


async def test_if_action_before_sunrise_with_offset(hass, calls):
    """Test if action was before offset."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'before': 'sunrise',
                'before_offset': '+1:00:00'
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    # sunrise: 13:32:43 UTC, sunset: 01:55:24 UTC
    # sunrise: 13:32:43 UTC, sunset: 01:56:46 UTC
    # now = sunrise + 1s + 1h -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 14, 32, 44, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    # now = sunrise + 1h -> 'before sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 14, 32, 43, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = UTC midnight -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 0, 0, 0, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = UTC midnight - 1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 15, 23, 59, 59, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = local midnight -> 'before sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = local midnight - 1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = sunset -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 1, 56, 48, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = sunset -1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 1, 56, 45, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)


async def test_if_action_before_sunset_with_offset(hass, calls):
    """Test if action was before offset."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'before': 'sunset',
                'before_offset': '+1:00:00'
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    # sunrise: 13:32:43 UTC, sunset: 01:55:24 UTC
    # now = sunset + 1s + 1h -> 'before sunset' with offset +1h not true
    now = datetime(2015, 9, 17, 2, 55, 25, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    # now = sunset + 1h -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 17, 2, 55, 24, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = UTC midnight -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 0, 0, 0, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = UTC midnight - 1s -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 23, 59, 59, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 3 == len(calls)

    # now = sunrise -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 13, 32, 43, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 4 == len(calls)

    # now = sunrise -1s -> 'before sunset' with offset +1h not true
    now = datetime(2015, 9, 16, 13, 32, 42, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 4 == len(calls)


async def test_if_action_after_sunrise_with_offset(hass, calls):
    """Test if action was after offset."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'after': 'sunrise',
                'after_offset': '+1:00:00'
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    # sunrise: 13:32:43 UTC, sunset: 01:55:24 UTC
    # now = sunrise - 1s + 1h -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 14, 32, 42, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    # now = sunrise + 1h -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 14, 32, 43, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = UTC noon -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 12, 0, 0, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = UTC noon - 1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 15, 11, 59, 59, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = local noon -> 'before sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 19, 1, 0, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = local noon - 1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 18, 59, 59, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = sunset -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 1, 55, 24, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = sunset + 1s -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 1, 55, 25, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)


async def test_if_action_after_sunset_with_offset(hass, calls):
    """Test if action was after offset."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'after': 'sunset',
                'after_offset': '+1:00:00'
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    # sunrise: 13:32:43 UTC, sunset: 01:55:24 UTC
    # now = sunset - 1s + 1h -> 'after sunset' with offset +1h not true
    now = datetime(2015, 9, 16, 2, 55, 23, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    # now = sunset + 1h -> 'after sunset' with offset +1h true
    now = datetime(2015, 9, 16, 2, 55, 24, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)

    # now = sunrise -> 'after sunset' with offset +1h true
    now = datetime(2015, 9, 16, 13, 32, 43, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)

    # now = sunrise + 1s -> 'after sunset' with offset +1h not true
    now = datetime(2015, 9, 16, 13, 32, 44, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 2 == len(calls)


async def test_if_action_before_and_after_during(hass, calls):
    """Test if action was before and after during."""
    await async_setup_component(hass, automation.DOMAIN, {
        automation.DOMAIN: {
            'trigger': {
                'platform': 'event',
                'event_type': 'test_event',
            },
            'condition': {
                'condition': 'sun',
                'after': 'sunrise',
                'before': 'sunset'
            },
            'action': {
                'service': 'test.automation'
            }
        }
    })

    now = datetime(2015, 9, 16, 13, 8, 51, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    now = datetime(2015, 9, 17, 2, 25, 18, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 0 == len(calls)

    now = datetime(2015, 9, 16, 16, tzinfo=dt_util.UTC)
    with patch('homeassistant.util.dt.utcnow',
               return_value=now):
        hass.bus.async_fire('test_event')
        await hass.async_block_till_done()
        assert 1 == len(calls)
