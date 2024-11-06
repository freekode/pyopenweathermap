import decimal
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CurrentAirPollution:
    date_time: datetime
    aqi: int
    co: decimal.Decimal
    no: decimal.Decimal
    no2: decimal.Decimal
    o3: decimal.Decimal
    so2: decimal.Decimal
    pm2_5: decimal.Decimal
    pm10: decimal.Decimal
    nh3: decimal.Decimal

@dataclass
class AirPollutionReport:
    current: CurrentAirPollution | None
    hourly_forecast: list[CurrentAirPollution]
