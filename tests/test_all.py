import os

import json
import pytest
from pyopenweathermap import RequestError, create_owm_client
from pyopenweathermap.data_converter import DataConverter

LATITUDE = '52.3731339'
LONGITUDE = '4.8903147'


@pytest.mark.network
@pytest.mark.asyncio
async def test_api_30():
    api_key = os.getenv('OWM_API_KEY')
    client = create_owm_client(api_key, 'v3.0')
    report = await client.get_weather(LATITUDE, LONGITUDE)
    assert report.current.date_time is not None
    assert report.hourly_forecast[0].condition.id is not None
    assert report.daily_forecast[0].condition.id is not None
    
    
@pytest.mark.network
@pytest.mark.asyncio
async def test_api_25():
    api_key = os.getenv('OWM_API_KEY')
    client = create_owm_client(api_key, 'v2.5')
    report = await client.get_weather(LATITUDE, LONGITUDE)
    assert report.current.date_time is not None
    assert report.hourly_forecast[0].condition.id is not None
    assert report.daily_forecast[0].condition.id is not None
    

@pytest.mark.network
@pytest.mark.asyncio
async def test_freemium_current_weather():
    api_key = os.getenv('OWM_API_KEY')
    client = create_owm_client(api_key, 'current')
    report = await client.get_weather(LATITUDE, LONGITUDE)
    assert report.current.date_time is not None
    assert len(report.hourly_forecast) is 0
    assert len(report.daily_forecast) is 0
    
    
@pytest.mark.network
@pytest.mark.asyncio
async def test_freemium_forecast_weather():
    api_key = os.getenv('OWM_API_KEY')
    client = create_owm_client(api_key, 'forecast')
    report = await client.get_weather(LATITUDE, LONGITUDE)
    assert report.current is None
    assert report.hourly_forecast[0].temperature is not None
    assert len(report.daily_forecast) is 0


@pytest.mark.network
@pytest.mark.asyncio
async def test_api_25_validate_key():
    client = create_owm_client('123', 'v2.5')
    assert await client.validate_key() is False


@pytest.mark.asyncio
async def test_request_error():
    api_key = os.getenv('OWM_API_KEY')
    client = create_owm_client(api_key, 'v3.0')
    with pytest.raises(RequestError) as error:
        await client.get_weather('100', LONGITUDE)
    assert error is not None


@pytest.mark.network
@pytest.mark.asyncio
async def test_api_key_validation():
    client = create_owm_client('123', 'v3.0')
    assert await client.validate_key() is False


def test_current_weather_converter():
    data = None
    with open('tests/onecall_current.json') as f:
        data = json.load(f)
    weather = DataConverter.onecall_to_current_weather(data)
    assert weather.date_time is not None
    assert weather.condition.id is not None


def test_hourly_weather_deserialization():
    data = None
    with open('tests/onecall_hourly.json') as f:
        data = json.load(f)
    weather = DataConverter.onecall_to_hourly_weather_forecast(data)
    assert weather.date_time is not None
    assert weather.condition.id is not None


def test_weather_deserialization():
    data = None
    with open('tests/freemium_current.json') as f:
        data = json.load(f)
    weather = DataConverter.free_to_current_weather(data)
    assert weather.date_time is not None
    assert weather.condition.id is not None


def test_forecast_deserialization():
    data = None
    with open('tests/freemium_forecast.json') as f:
        data = json.load(f)
    weather = DataConverter.free_to_hourly_weather_forecast(data)
    assert weather.date_time is not None
    assert weather.condition.id is not None
