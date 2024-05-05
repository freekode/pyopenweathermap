from aiohttp import ClientSession

from .data_converter import DataConverter
from .exception import UnauthorizedError, RequestError, TooManyRequestsError
from .weather import WeatherReport
import logging

API_V30_URL = 'https://api.openweathermap.org/data/3.0/onecall'
API_V25_URL = 'https://api.openweathermap.org/data/2.5/onecall'
WEATHER_TYPES = {'current', 'minutely', 'hourly', 'daily', 'alerts'}


class OWMClient:
    session: ClientSession | None = None
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
        self.request_timeout = request_timeout

    async def get_weather(self, lat, lon, weather_types=None) -> WeatherReport:
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

    async def _request(self, url):
        self.logger.debug('Requesting url: ' + url)
        async with ClientSession() as session:
            try:
                async with session.get(url=url, timeout=self.request_timeout) as response:
                    response_json = await response.json()
                    if response.status == 200:
                        return response_json
                    elif response.status == 400:
                        raise RequestError(response_json.get('message'))
                    elif response.status == 401:
                        raise UnauthorizedError(response_json.get('message'))
                    elif response.status == 404:
                        raise RequestError(response_json.get('message'))
                    elif response.status == 429:
                        raise TooManyRequestsError(response_json.get('message'))
                    else:
                        raise RequestError("Unknown status code: {}".format(response.status))
            except RequestError as error:
                raise error
            except TimeoutError:
                raise RequestError("Request timeout")
            except Exception as error:
                raise RequestError(error) from error

    def _get_url(self, lat, lon, exclude):
        return (f"{self.main_url}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"exclude={','.join(exclude)}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
