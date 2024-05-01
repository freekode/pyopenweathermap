import decimal
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DailyTemperature:
    day: decimal.Decimal
    min: decimal.Decimal
    max: decimal.Decimal
    night: decimal.Decimal
    evening: decimal.Decimal
    morning: decimal.Decimal


@dataclass
class WeatherCondition:
    id: int
    main: str
    description: str
    icon: str


@dataclass
class CurrentWeather:
    date_time: datetime
    temperature: decimal.Decimal
    feels_like: decimal.Decimal
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal
    cloud_coverage: int
    visibility: int
    wind_speed: decimal.Decimal
    wind_gust: int
    wind_bearing: decimal.Decimal
    rain: dict
    snow: dict
    condition: WeatherCondition


@dataclass
class HourlyWeatherForecast:
    date_time: datetime
    temperature: decimal.Decimal
    feels_like: decimal.Decimal
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal
    cloud_coverage: int
    visibility: int
    wind_speed: decimal.Decimal
    wind_gust: decimal.Decimal
    wind_bearing: int
    precipitation_probability: decimal.Decimal
    rain: dict
    snow: dict
    condition: WeatherCondition


@dataclass
class DailyWeatherForecast:
    date_time: datetime
    summary: str
    temperature: DailyTemperature
    feels_like: DailyTemperature
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal
    cloud_coverage: int
    wind_speed: decimal.Decimal
    wind_gust: decimal.Decimal
    wind_bearing: int
    precipitation_probability: decimal.Decimal
    rain: decimal.Decimal
    snow: decimal.Decimal
    condition: WeatherCondition


@dataclass
class WeatherReport:
    current: CurrentWeather
    hourly_forecast: list[HourlyWeatherForecast]
    daily_forecast: list[DailyWeatherForecast]
