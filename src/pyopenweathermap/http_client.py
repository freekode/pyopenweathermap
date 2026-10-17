import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiohttp import ClientSession, ContentTypeError

from .exception import UnauthorizedError, RequestError, TooManyRequestsError


class HttpClient:
    request_timeout: int
    logger = logging.getLogger(__name__)

    def __init__(self, request_timeout=20):
        self.request_timeout = request_timeout

    async def request(self, url):
        parts = urlsplit(url)
        safe_query = urlencode([(key, '[redacted]' if key == 'appid' else value)
                                for key, value in parse_qsl(parts.query)])
        self.logger.debug('Requesting url: %s', urlunsplit(parts._replace(query=safe_query)))
        async with ClientSession() as session:
            try:
                async with session.get(url=url, timeout=self.request_timeout, allow_redirects=False) as response:
                    try:
                        response_json = await response.json()
                    except (ValueError, ContentTypeError):
                        # aiohttp content-type errors contain the credentialed
                        # request URL. Do not expose it through exception chains.
                        if response.status == 200:
                            raise RequestError('Invalid JSON response') from None
                        response_json = {}
                    if response.status == 200:
                        return response_json
                    message = response_json.get('message') if isinstance(response_json, dict) else None
                    message = message or f'HTTP status code: {response.status}'
                    if response.status == 401:
                        raise UnauthorizedError(message)
                    if response.status == 429:
                        raise TooManyRequestsError(message)
                    raise RequestError(message)
            except RequestError:
                raise
            except TimeoutError:
                raise RequestError('Request timeout') from None
            except Exception as error:
                raise RequestError(f'Request failed: {type(error).__name__}') from None
