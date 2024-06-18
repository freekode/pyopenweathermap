from aiohttp import ClientSession

from .exception import UnauthorizedError, RequestError, TooManyRequestsError
import logging

class HttpClient:
    request_timeout: int
    logger = logging.getLogger(__name__)

    def __init__(self, request_timeout=20):
        self.request_timeout = request_timeout    
    
    async def request(self, url):
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
