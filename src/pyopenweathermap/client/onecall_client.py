from collections.abc import Callable
from math import isfinite
from typing import TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .owm_abstract_client import OWMClient
from ..data_converter import DataConverter
from ..exception import RequestError, UnauthorizedError
from ..weather import WeatherReport
from ..air_pollution import AirPollutionReport

API_URL = 'https://api.openweathermap.org/data/3.0/onecall'
V4_API_URL = 'https://api.openweathermap.org/data/4.0/onecall'
WeatherT = TypeVar('WeatherT')


class OWMOneCallClient(OWMClient):
    def __init__(self, api_key, api_version, units="metric", lang='en'):
        super().__init__()
        self.api_key = api_key
        self.api_version = api_version
        self.units = units
        self.lang = lang

    async def get_weather(self, lat, lon) -> WeatherReport:
        if self.api_version == 'v4.0':
            return await self._get_v4_weather(lat, lon)

        json_response = await self.http_client.request(self._get_url(lat, lon))
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

    async def _get_v4_weather(self, lat, lon) -> WeatherReport:
        response = await self.http_client.request(self._get_url(lat, lon))
        rows = self._v4_data(response)
        current = self._convert_v4(rows[0], DataConverter.onecall_to_current_weather) if rows else None
        # Keep the legacy report horizon. Requests are sequential so failures do
        # not leave other billable requests running in the background.
        minutely = await self._v4_forecast(
            lat, lon, 'timeline/1min', 60, 60,
            DataConverter.onecall_to_minutely_weather_forecast,
        )
        hourly = await self._v4_forecast(
            lat, lon, 'timeline/1h', 48, 3600,
            DataConverter.onecall_to_hourly_weather_forecast,
        )
        daily = await self._v4_forecast(
            lat, lon, 'timeline/1day', 8, 86400,
            DataConverter.onecall_to_daily_weather_forecast,
        )
        return WeatherReport(current, minutely, hourly, daily)

    async def _v4_forecast(
        self, lat, lon, endpoint, count, interval, converter: Callable[[dict], WeatherT],
    ) -> list[WeatherT]:
        url = self._get_url(lat, lon, endpoint)
        visited = set()
        result: list[WeatherT] = []
        last_dt = None
        end_dt = None
        while len(result) < count:
            # Canonicalize query order so a reordered repeated link also stops.
            identity = (urlsplit(url).path, tuple(sorted(parse_qsl(urlsplit(url).query))))
            if identity in visited:
                raise RequestError('Repeated One Call 4.0 pagination link')
            visited.add(identity)
            response = await self.http_client.request(url)
            rows = self._v4_data(response)
            if not rows:
                break
            previous_dt = None
            added = 0
            for row in rows:
                dt = row.get('dt')
                if not isinstance(dt, int) or isinstance(dt, bool):
                    raise RequestError('Invalid One Call 4.0 forecast timestamp')
                if previous_dt is not None and dt < previous_dt:
                    raise RequestError('Unordered One Call 4.0 forecast page')
                previous_dt = dt
                if end_dt is None:
                    end_dt = dt + count * interval
                if dt >= end_dt:
                    return result
                if last_dt is not None and dt <= last_dt:
                    continue  # Pagination may overlap at the page boundary.
                if endpoint == 'timeline/1day':
                    self._validate_v4_daily_precipitation(row)
                result.append(self._convert_v4(row, converter))
                last_dt = dt
                added += 1
                if len(result) == count:
                    return result
            next_url = response.get('next')
            if next_url is None or next_url == '':
                break
            if not added:
                raise RequestError('One Call 4.0 pagination made no progress')
            # Every continued page adds a record, so even changing links cannot
            # cause unbounded requests. Stop at the count/time horizon above.
            url = self._v4_next_url(next_url, lat, lon, endpoint)
        return result

    @staticmethod
    def _v4_data(response):
        if not isinstance(response, dict) or not isinstance(response.get('data'), list):
            raise RequestError('Invalid One Call 4.0 response: expected a data array')
        if any(not isinstance(row, dict) for row in response['data']):
            raise RequestError('Invalid One Call 4.0 response: expected data objects')
        return response['data']

    @staticmethod
    def _convert_v4(row, converter: Callable[[dict], WeatherT]) -> WeatherT:
        try:
            return converter(row)
        except (KeyError, TypeError, ValueError, IndexError, OverflowError, OSError) as error:
            raise RequestError('Invalid One Call 4.0 weather record') from error

    @staticmethod
    def _validate_v4_daily_precipitation(row):
        # The migration guide specifies daily scalar totals, but the reference
        # also lists rain.1h/snow.1h. Never mislabel an hourly rate as a daily total.
        for field in ('rain', 'snow'):
            value = row.get(field, 0)
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or (isinstance(value, float) and not isfinite(value)) or value < 0):
                raise RequestError(
                    f'Unsupported One Call 4.0 daily {field}: expected a numeric daily total'
                )

    def _v4_next_url(self, next_url, lat, lon, endpoint):
        if not isinstance(next_url, str):
            raise RequestError('Invalid One Call 4.0 pagination link')
        try:
            parts = urlsplit(next_url)
        except ValueError as error:
            raise RequestError('Invalid One Call 4.0 pagination link') from error
        expected = urlsplit(f'{V4_API_URL}/{endpoint}')
        if (parts.scheme != 'https' or parts.netloc != expected.netloc
                or parts.path != expected.path or parts.fragment):
            raise RequestError('Unsafe One Call 4.0 pagination link')
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        # Some documented links omit units/lang. Preserve the caller's options
        # and location/key even if a next link omits or changes them.
        query.update(self._query_params(lat, lon))
        return urlunsplit(parts._replace(query=urlencode(query)))

    async def get_air_pollution(self, lat, lon) -> AirPollutionReport:
        raise NotImplementedError('One Call client does not have get_air_pollution()')

    async def validate_key(self) -> bool:
        url = self._get_url(50.06, 14.44)
        if self.api_version != 'v4.0':
            url += '&exclude=current,minutely,hourly,daily,alerts'
        try:
            await self.http_client.request(url)
            return True
        except UnauthorizedError:
            return False

    def _query_params(self, lat, lon):
        return {'lat': lat, 'lon': lon, 'appid': self.api_key,
                'units': self.units, 'lang': self.lang}

    def _get_url(self, lat, lon, endpoint='current'):
        api_url = f'{V4_API_URL}/{endpoint}' if self.api_version == 'v4.0' else API_URL
        return f'{api_url}?{urlencode(self._query_params(lat, lon))}'
