from aiohttp import ClientSession

from .converter import DataConverter
from ..exception import UnauthorizedError
from ..weather import WeatherReport
from ..owm_client import OWMClient, WEATHER_TYPES

API_URL = 'https://api.openweathermap.org/data/3.0/onecall'


class OWMClientV3(OWMClient):
    session: ClientSession | None = None
    request_timeout: int

    def __init__(self, api_key, units="metric", lang='en', request_timeout=20):
        self.api_key = api_key
        self.units = units
        self.lang = lang
        self.request_timeout = request_timeout

    async def get_weather(self, lat, lon, weather_types=set()) -> WeatherReport:
        if weather_types is None:
            exclude_weather_types = {}
        else:
            exclude_weather_types = WEATHER_TYPES - set(weather_types)

        url = self._get_url(lat, lon, exclude_weather_types)
        json_response = await self._request(url)

        current, hourly, daily = None, [], []
        if json_response.get('current') is not None:
            current = DataConverter.to_current_weather(json_response['current'])
        if json_response.get('hourly') is not None:
            hourly = [DataConverter.to_hourly_weather_forecast(item) for item in json_response['hourly']]
        if json_response.get('daily') is not None:
            daily = [DataConverter.to_daily_weather_forecast(item) for item in json_response['daily']]

        return WeatherReport(current, hourly, daily)

    async def validate_key(self) -> bool:
        url = self._get_url(50.06, 14.44, WEATHER_TYPES)
        try:
            await self._request(url)
            return True
        except UnauthorizedError:
            return False

    def _get_url(self, lat, lon, exclude):
        return (f"{API_URL}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"exclude={','.join(exclude)}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
