from abc import ABC, abstractmethod
from ..weather import WeatherReport
from ..air_pollution import AirPollutionReport
from ..http_client import HttpClient


class OWMClient(ABC):
    http_client: HttpClient

    def __init__(self) -> None:
        self.http_client = HttpClient()

    @abstractmethod
    async def get_weather(self, lat, lon) -> WeatherReport:
        pass

    @abstractmethod
    async def get_air_pollution(self, lat, lon) -> AirPollutionReport:
        pass

    @abstractmethod
    async def validate_key(self) -> bool:
        pass
