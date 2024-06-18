from .owm_abstract_client import OWMClient
from ..data_converter import DataConverter
from ..exception import UnauthorizedError
from ..weather import WeatherReport

V30_API_URL = 'https://api.openweathermap.org/data/3.0/onecall'
V25_API_URL = 'https://api.openweathermap.org/data/2.5/onecall'


class OWMOneCallClient(OWMClient):
    def __init__(self, api_key, api_version, units="metric", lang='en'):
        super().__init__()
        self.api_key = api_key
        self.api_version = api_version
        self.units = units
        self.lang = lang

    async def get_weather(self, lat, lon) -> WeatherReport:
        url = self._get_url(lat, lon)
        json_response = await self.http_client.request(url)

        current, hourly, daily = None, [], []
        if json_response.get('current') is not None:
            current = DataConverter.onecall_to_current_weather(json_response['current'])
        if json_response.get('hourly') is not None:
            hourly = [DataConverter.onecall_to_hourly_weather_forecast(item) for item in json_response['hourly']]
        if json_response.get('daily') is not None:
            daily = [DataConverter.onecall_to_daily_weather_forecast(item) for item in json_response['daily']]

        return WeatherReport(current, hourly, daily)

    async def validate_key(self) -> bool:
        url = (f"{self._get_url(50.06, 14.44)}"
              f"&exclude=current,minutely,hourly,daily,alerts)")
        try:
            await self.http_client.request(url)
            return True
        except UnauthorizedError:
            return False

    def _get_url(self, lat, lon):
        url = V30_API_URL if self.api_version == 'v3.0' else V25_API_URL 
        return (f"{url}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
