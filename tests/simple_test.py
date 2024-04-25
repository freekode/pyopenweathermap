import os

import pytest

from src.pyopenweathermap import (
    OWMClient
)


@pytest.mark.asyncio
async def t2est_my_test():
    api_key = os.getenv("OWM_API_KEY")
    client = OWMClient(api_key, 'metric')
    report = await client.one_call('51.051', '16.202', ['current', 'hourly', 'daily'])
    assert report.current.datetime is not None
    assert len(report.hourly) > 0
    assert len(report.daily) > 0


@pytest.mark.asyncio
async def test_api_key_validation():
    client = OWMClient('123', 'metric')
    assert await client.validate_key() is False
