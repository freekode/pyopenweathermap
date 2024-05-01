from .converter import DataConverter
from ..owm_client import OWMClient, WEATHER_TYPES
from ..weather import WeatherReport
from ..exception import UnauthorizedError

CURRENT_WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
HOURLY_FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
DAILY_FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast/daily'


class OWMClientV25(OWMClient):
    def __init__(self, api_key, units="metric", lang='en', request_timeout=20):
        self.api_key = api_key
        self.units = units
        self.lang = lang
        self.request_timeout = request_timeout

    async def get_weather(self, lat, lon, weather_types=set()) -> WeatherReport:
        current, hourly, daily = None, [], []
        if len(weather_types) == 0:
            weather_types = WEATHER_TYPES
        if 'current' in weather_types:
            url = self._get_url(CURRENT_WEATHER_URL, lat, lon)
            json_response = await self._request(url)
            current = DataConverter.to_current_weather(json_response)
        if 'hourly' in weather_types:
            url = self._get_url(HOURLY_FORECAST_URL, lat, lon)
            json_response = await self._request(url)
            hourly = [DataConverter.to_hourly_weather_forecast(item) for item in json_response['list']]
        if 'daily' in weather_types:
            url = self._get_url(DAILY_FORECAST_URL, lat, lon)
            json_response = await self._request(url)
            daily = [DataConverter.to_daily_weather_forecast(item) for item in json_response['list']]

        return WeatherReport(current, hourly, daily)

    async def validate_key(self) -> bool:
        url = self._get_url(CURRENT_WEATHER_URL, 50.06, 14.44)
        try:
            await self._request(url)
            return True
        except UnauthorizedError:
            return False

    def _get_url(self, url, lat, lon):
        return (f"{url}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
