from aiohttp import ClientSession

from .exception import RequestError, UnauthorizedError, TooManyRequestsError
from .weather import WeatherReport, CurrentWeather, HourlyWeatherForecast, DailyWeatherForecast

API_URL = 'https://api.openweathermap.org/data/3.0/onecall'
WEATHER_TYPES = {'current', 'minutely', 'hourly', 'daily', 'alerts'}


class OWMClient:
    session: ClientSession | None = None
    request_timeout: int = 10

    def __init__(self, api_key, units="metric", lang='en'):
        self.api_key = api_key
        self.units = units
        self.lang = lang

    async def get_weather(self, lat, lon, weather_types=None) -> WeatherReport:
        if weather_types is None:
            exclude_weather_types = {}
        else:
            exclude_weather_types = WEATHER_TYPES - set(weather_types)

        url = self._get_url(lat, lon, exclude_weather_types)
        json_response = await self._request(url)

        current, hourly, daily = None, None, None
        if json_response.get('current') is not None:
            current = CurrentWeather(**json_response['current'])
        if json_response.get('hourly') is not None:
            hourly = [HourlyWeatherForecast(**item) for item in json_response['hourly']]
        if json_response.get('daily') is not None:
            daily = [DailyWeatherForecast(**item) for item in json_response['daily']]

        return WeatherReport(current, hourly, daily)

    async def validate_key(self) -> bool:
        url = self._get_url(50.06, 14.44, WEATHER_TYPES)
        try:
            await self._request(url)
            return True
        except UnauthorizedError:
            return False

    async def _request(self, url):
        async with ClientSession() as session:
            try:
                async with session.get(url=url, timeout=self.request_timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise UnauthorizedError
                    elif response.status == 404:
                        raise RequestError("Not Found")
                    elif response.status == 429:
                        raise TooManyRequestsError
                    else:
                        raise RequestError("Unknown Error")
            except TimeoutError:
                raise RequestError("Request timeout")

    def _get_url(self, lat, lon, exclude):
        return (f"{API_URL}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"exclude={','.join(exclude)}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"lang={self.lang}")
