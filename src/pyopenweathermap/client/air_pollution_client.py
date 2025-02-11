from ..data_converter import DataConverter
from ..exception import UnauthorizedError
from ..air_pollution import AirPollutionReport

CURRENT_AIR_POLLUTION_API_URL = 'https://api.openweathermap.org/data/2.5/air_pollution'
FORECAST_API_URL = 'https://api.openweathermap.org/data/2.5/air_pollution/forecast'

class OWMAirPollutionClient:
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    async def get_air_pollution(self, lat, lon) -> AirPollutionReport:
        url = self._get_url(lat, lon, 'current')
        current_json = await self.http_client.request(url)
        current = DataConverter.air_pollution_current(current_json)

        url = self._get_url(lat, lon, 'forecast')
        forecast_json = await self.http_client.request(url)
        hourly = [DataConverter.air_pollution_hourly(item) for item in forecast_json['list']]

        return AirPollutionReport(current, hourly)

    async def validate_key(self) -> bool:
        url = self._get_url(50.06, 14.44, 'api_type')
        try:
            await self.http_client.request(url)
            return True
        except UnauthorizedError:
            return False

    def _get_url(self, lat, lon, api_type):
        url = CURRENT_AIR_POLLUTION_API_URL if api_type == 'current' else FORECAST_API_URL
        return (f"{url}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}")
