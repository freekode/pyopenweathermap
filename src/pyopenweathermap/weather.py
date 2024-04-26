import decimal
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field


class DailyTemperature(BaseModel):
    day: decimal.Decimal
    min: decimal.Decimal = None
    max: decimal.Decimal = None
    night: decimal.Decimal
    evening: decimal.Decimal = Field(alias='eve')
    morning: decimal.Decimal = Field(alias='morn')


class WeatherCondition(BaseModel):
    id: int
    main: str
    description: str
    icon: str


class CurrentWeather(BaseModel):
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
    wind_gust: decimal.Decimal = None
    wind_deg: int
    rain: dict = {}
    snow: dict = {}
    condition: list[WeatherCondition] = Field(alias='weather')

    def get_weather(self):
        return self.condition[0]


class HourlyWeatherForecast(BaseModel):
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
    wind_gust: decimal.Decimal = None
    wind_deg: int
    precipitation_probability: decimal.Decimal = Field(alias='pop', default=0)
    rain: dict = {}
    snow: dict = {}
    condition: list[WeatherCondition] = Field(alias='weather')

    def get_weather(self):
        return self.condition[0]


class DailyWeatherForecast(BaseModel):
    date_time: datetime = Field(alias='dt')
    summary: str
    temperature: DailyTemperature = Field(alias='temp')
    feels_like: DailyTemperature
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal = Field(alias='uvi')
    clouds: int
    wind_speed: decimal.Decimal
    wind_gust: decimal.Decimal = None
    wind_deg: int
    precipitation_probability: decimal.Decimal = Field(alias='pop', default=0)
    rain: decimal.Decimal = 0
    snow: decimal.Decimal = 0
    condition: list[WeatherCondition] = Field(alias='weather')

    def get_weather(self):
        return self.condition[0]


@dataclass
class WeatherReport:
    current: CurrentWeather
    hourly_forecast: list[HourlyWeatherForecast]
    daily_forecast: list[DailyWeatherForecast]
