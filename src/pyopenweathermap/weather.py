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
    dew_point: decimal.Decimal | None
    uv_index: decimal.Decimal | None
    cloud_coverage: int
    visibility: int | None
    wind_speed: decimal.Decimal
    wind_gust: int | None
    wind_bearing: decimal.Decimal
    rain: dict | None
    snow: dict | None
    condition: WeatherCondition


@dataclass
class MinutelyWeatherForecast:
    date_time: datetime
    precipitation: decimal.Decimal


@dataclass
class HourlyWeatherForecast:
    date_time: datetime
    temperature: decimal.Decimal
    feels_like: decimal.Decimal
    pressure: int
    humidity: int
    dew_point: decimal.Decimal | None
    uv_index: decimal.Decimal | None
    cloud_coverage: int
    visibility: int | None
    wind_speed: decimal.Decimal
    wind_gust: decimal.Decimal | None
    wind_bearing: int
    precipitation_probability: decimal.Decimal
    rain: dict | None
    snow: dict | None
    condition: WeatherCondition


@dataclass
class DailyWeatherForecast:
    date_time: datetime
    summary: str | None
    temperature: DailyTemperature
    feels_like: DailyTemperature
    pressure: int
    humidity: int
    dew_point: decimal.Decimal
    uv_index: decimal.Decimal
    cloud_coverage: int
    wind_speed: decimal.Decimal
    wind_gust: decimal.Decimal | None
    wind_bearing: int
    precipitation_probability: decimal.Decimal
    rain: decimal.Decimal
    snow: decimal.Decimal
    condition: WeatherCondition


@dataclass
class WeatherReport:
    current: CurrentWeather | None
    minutely_forecast: list[MinutelyWeatherForecast]
    hourly_forecast: list[HourlyWeatherForecast]
    daily_forecast: list[DailyWeatherForecast]
