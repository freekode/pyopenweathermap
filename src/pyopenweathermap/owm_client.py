from abc import ABC, abstractmethod

from aiohttp import ClientSession

from .exception import RequestError, TooManyRequestsError, UnauthorizedError

WEATHER_TYPES = {'current', 'minutely', 'hourly', 'daily', 'alerts'}


class OWMClient(ABC):
    @abstractmethod
    async def get_weather(self, lat, lon, weather_types=set()):
        pass

    @abstractmethod
    async def validate_key(self):
        pass

    async def _request(self, url):
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
            except TimeoutError:
                raise RequestError("Request timeout")
            except RequestError as error:
                raise error
            except Exception as error:
                raise RequestError(error) from error
