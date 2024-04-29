import os

import pytest

from pyopenweathermap import CurrentWeather, HourlyWeatherForecast, RequestError, OWMClient


@pytest.mark.asyncio
async def test_get_weather():
    api_key = os.getenv('OWM_API_KEY')
    client = OWMClient(api_key, 'metric')
    report = await client.get_weather('52.3731339', '4.8903147', ['current', 'hourly', 'daily'])
    assert report.current.date_time is not None
    assert report.hourly_forecast[0].get_weather().id is not None
    assert report.daily_forecast[0].get_weather().id is not None
    print(report.hourly_forecast[0].date_time.timestamp())


@pytest.mark.asyncio
async def test_request_error():
    api_key = os.getenv('OWM_API_KEY')
    client = OWMClient(api_key, 'metric')
    with pytest.raises(RequestError) as error:
        await client.get_weather('100', '4.8903147', ['current', 'hourly', 'daily'])
    assert error is not None


@pytest.mark.asyncio
async def test_api_key_validation():
    client = OWMClient('123', 'metric')
    assert await client.validate_key() is False


def test_current_weather_deserialization():
    data = {'dt': 1714063536, 'sunrise': 1714018842, 'sunset': 1714071341, 'temp': 6.84, 'feels_like': 2.07,
            'pressure': 1000, 'humidity': 82, 'dew_point': 3.99, 'uvi': 0.13, 'clouds': 75, 'visibility': 10000,
            'wind_speed': 9.83, 'wind_deg': 199,
            'weather': [{'id': 803, 'main': 'Clouds', 'description': 'broken clouds', 'icon': '04d'}]}
    weather = CurrentWeather(**data)
    assert weather.date_time is not None
    assert weather.get_weather().id is not None


def test_hourly_weather_deserialization():
    data = {'dt': 1714168800, 'temp': 5.82, 'feels_like': 5.82, 'pressure': 1007, 'humidity': 87, 'dew_point': 3.85,
            'uvi': 0, 'clouds': 100, 'visibility': 10000, 'wind_speed': 1.02, 'wind_deg': 167, 'wind_gust': 1.39,
            'weather': [{'id': 500, 'main': 'Rain', 'description': 'light rain', 'icon': '10n'}], 'pop': 0.79}
    weather = HourlyWeatherForecast(**data)
    assert weather.date_time is not None
    assert weather.get_weather().id is not None
    assert weather.rain is not None
