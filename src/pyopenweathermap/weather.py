from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass
class HourlyWeather:
    datetime: datetime = field(metadata=config(
        encoder=datetime.isoformat,
        decoder=datetime.fromtimestamp,
        field_name="dt"))
    temperature: str = field(metadata=config(field_name="temp"))
    feels_like: str
    pressure: str
    humidity: str
    dew_point: str
    uv_index: str = field(metadata=config(field_name="uvi"))
    clouds: str
    visibility: str
    wind_speed: str
    wind_deg: str
    wind_gust: str
    condition: object = field(metadata=config(field_name="weather"))
    # precipitation_probability: Optional[str] = field(metadata=config(field_name="pop"))
    rain: Optional[object] = None
    snow: Optional[object] = None


@dataclass_json
@dataclass
class DailyWeather:
    datetime: datetime = field(metadata=config(
        encoder=datetime.isoformat,
        decoder=datetime.fromtimestamp,
        field_name="dt"))
    summary: str
    temperature: object = field(metadata=config(field_name="temp"))
    feels_like: object
    pressure: str
    humidity: str
    dew_point: str
    uv_index: str = field(metadata=config(field_name="uvi"))
    clouds: str
    wind_speed: str
    wind_deg: str
    wind_gust: str
    condition: object = field(metadata=config(field_name="weather"))
    # precipitation_probability: Optional[str] = field(metadata=config(field_name="pop"))
    rain: Optional[str] = None
    snow: Optional[str] = None


@dataclass
class WeatherReport:
    current: HourlyWeather
    hourly: list[HourlyWeather]
    daily: list[DailyWeather]
