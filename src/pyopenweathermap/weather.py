import decimal
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field


class HourlyWeather(BaseModel):
    date_time: datetime = Field(alias='dt')
    temperature: decimal.Decimal = Field(alias='temp')
    feels_like: decimal.Decimal
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal = Field(alias='uvi')
    clouds: int
    visibility: int
    wind_speed: decimal.Decimal
    wind_deg: decimal.Decimal
    wind_gust: decimal.Decimal = None
    precipitation_probability: int = None
    rain: object = None
    snow: object = None
    condition: object = Field(alias='weather')


class DailyWeather(BaseModel):
    date_time: datetime = Field(alias='dt')
    temperature: object = Field(alias='temp')
    feels_like: object
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal = Field(alias='uvi')
    clouds: int
    wind_speed: decimal.Decimal
    wind_deg: decimal.Decimal
    wind_gust: decimal.Decimal = None
    precipitation_probability: int = None
    rain: object = None
    snow: object = None
    condition: object = Field(alias='weather')
    summary: str


@dataclass
class WeatherReport:
    current: HourlyWeather
    hourly: list[HourlyWeather]
    daily: list[DailyWeather]
