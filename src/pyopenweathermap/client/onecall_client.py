from .owm_abstract_client import OWMClient
from ..data_converter import DataConverter
from ..exception import UnauthorizedError
from ..weather import WeatherReport
from ..air_pollution import AirPollutionReport

API_URL = 'https://api.openweathermap.org/data/3.0/onecall'


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

        current, minutely, hourly, daily = None, [], [], []
        if json_response.get('current') is not None:
            current = DataConverter.onecall_to_current_weather(json_response['current'])
        if json_response.get('minutely') is not None:
            minutely = [DataConverter.onecall_to_minutely_weather_forecast(item) for item in json_response['minutely']]
        if json_response.get('hourly') is not None:
            hourly = [DataConverter.onecall_to_hourly_weather_forecast(item) for item in json_response['hourly']]
        if json_response.get('daily') is not None:
            daily = [DataConverter.onecall_to_daily_weather_forecast(item) for item in json_response['daily']]

        return WeatherReport(current, minutely, hourly, daily)

    async def get_air_pollution(self, lat, lon) -> AirPollutionReport:
        raise NotImplementedError('free client does not have get_air_pollution()')

    async def validate_key(self) -> bool:
        url = (f"{self._get_url(50.06, 14.44)}"
              f"&exclude=current,minutely,hourly,daily,alerts)")
        try:
            await self.http_client.request(url)
            return True
        except UnauthorizedError:
            return False

    def _get_url(self, lat, lon):
        return (f"{API_URL}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
