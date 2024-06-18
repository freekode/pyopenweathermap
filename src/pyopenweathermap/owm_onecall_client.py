from .data_converter import DataConverter
from .exception import UnauthorizedError
from .weather import WeatherReport
from .http_client import HttpClient
import logging

API_V30_URL = 'https://api.openweathermap.org/data/3.0/onecall'
API_V25_URL = 'https://api.openweathermap.org/data/2.5/onecall'


class OWMClient:
    http_client: HttpClient
    request_timeout: int
    logger = logging.getLogger(__name__)

    def __init__(self, api_key, api_version, units="metric", lang='en', request_timeout=20):
        self.logger.info('Initializing OWMClient with api version: ' + str(api_version))
        if api_version == 'v3.0':
            self.main_url = API_V30_URL
        elif api_version == 'v2.5':
            self.main_url = API_V25_URL
        else:
            raise Exception('Unsupported API version ' + str(api_version))
        self.api_key = api_key
        self.units = units
        self.lang = lang
        self.http_client = HttpClient(request_timeout)

    async def get_weather(self, lat, lon) -> WeatherReport:
        url = self._get_url(lat, lon)
        json_response = await self.http_client.request(url)

        current, hourly, daily = None, [], []
        if json_response.get('current') is not None:
            current = DataConverter.to_current_weather(json_response['current'])
        if json_response.get('hourly') is not None:
            hourly = [DataConverter.to_hourly_weather_forecast(item) for item in json_response['hourly']]
        if json_response.get('daily') is not None:
            daily = [DataConverter.to_daily_weather_forecast(item) for item in json_response['daily']]

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
        return (f"{self.main_url}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
