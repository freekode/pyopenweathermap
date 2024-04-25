import os

import pytest

from pyopenweathermap import HourlyWeather
from src.pyopenweathermap import (
    OWMClient
)


@pytest.mark.asyncio
async def test_get_weather():
    api_key = os.getenv("OWM_API_KEY")
    client = OWMClient(api_key, 'metric')
    report = await client.get_weather('51.051', '16.202', ['current', 'hourly', 'daily'])
    assert report.current.datetime is not None
    assert len(report.hourly) > 0
    assert len(report.daily) > 0


@pytest.mark.asyncio
async def test_api_key_validation():
    client = OWMClient('123', 'metric')
    assert await client.validate_key() is False


def test_my_test():
    current = HourlyWeather.from_dict(
        {'dt': 1714063536, 'sunrise': 1714018842, 'sunset': 1714071341, 'temp': 6.84, 'feels_like': 2.07,
         'pressure': 1000, 'humidity': 82, 'dew_point': 3.99, 'uvi': 0.13, 'clouds': 75, 'visibility': 10000,
         'wind_speed': 9.83, 'wind_deg': 199,
         'weather': [{'id': 803, 'main': 'Clouds', 'description': 'broken clouds', 'icon': '04d'}]})
    assert current.datetime is not None
