from .owm_abstract_client import OWMClient
from ..data_converter import DataConverter
from ..exception import UnauthorizedError
from ..weather import WeatherReport

CURRENT_WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_API_URL = 'https://api.openweathermap.org/data/2.5/forecast'


class OWMFreeClient(OWMClient):
    def __init__(self, api_key, api_type, units="metric", lang='en'):
        super().__init__()
        self.api_key = api_key
        self.api_type = api_type
        self.units = units
        self.lang = lang

    async def get_weather(self, lat, lon) -> WeatherReport:
        url = self._get_url(lat, lon)
        json_response = await self.http_client.request(url)

        current, hourly = None, []
        if self.api_type == 'current':
            current = DataConverter.free_to_current_weather(json_response)
        else:
            hourly = [DataConverter.free_to_hourly_weather_forecast(item) for item in json_response['list']]
        return WeatherReport(current, hourly, [])

    async def validate_key(self) -> bool:
        url = self._get_url(50.06, 14.44)
        try:
            await self.http_client.request(url)
            return True
        except UnauthorizedError:
            return False

    def _get_url(self, lat, lon):
        url = CURRENT_WEATHER_API_URL if self.api_type == 'current' else FORECAST_API_URL
        return (f"{url}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
