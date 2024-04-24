import pytest

from src.pyopenweathermap import OWMClient
from src.pyopenweathermap import OWMException


@pytest.mark.asyncio
async def test_my_test():
    client = OWMClient('123', 'metric')
    report = await client.one_call('51.051', '16.202', ['current', 'hourly', 'daily'])
    assert report.current.datetime is not None
    assert len(report.hourly) > 0
    assert len(report.daily) > 0


@pytest.mark.asyncio
async def test_api_key_validation():
    client = OWMClient('123', 'metric')
    with pytest.raises(OWMException):
        await client.validate_key()
