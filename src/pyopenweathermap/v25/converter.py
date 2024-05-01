from datetime import datetime

from ..weather import CurrentWeather, WeatherCondition, HourlyWeatherForecast, DailyWeatherForecast, DailyTemperature


class DataConverter:
    @staticmethod
    def to_current_weather(json):
        return CurrentWeather(
            date_time=datetime.fromtimestamp(json['dt']),
            temperature=json['main']['temp'],
            feels_like=json['main']['feels_like'],
            pressure=json['main']['pressure'],
            humidity=json['main']['humidity'],
            dew_point=json.get('dew_point'),
            uv_index=json.get('uvi'),
            cloud_coverage=json['clouds']['all'],
            visibility=json.get('visibility'),
            wind_speed=json.get('wind').get('speed'),
            wind_gust=json.get('wind').get('gust'),
            wind_bearing=json.get('wind').get('deg'),
            rain=json.get('rain'),
            snow=json.get('snow'),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )

    @staticmethod
    def to_hourly_weather_forecast(json):
        return HourlyWeatherForecast(
            date_time=datetime.fromtimestamp(json['dt']),
            temperature=json['main']['temp'],
            feels_like=json['main']['feels_like'],
            pressure=json['main']['pressure'],
            humidity=json['main']['humidity'],
            dew_point=json.get('dew_point'),
            uv_index=json.get('uvi'),
            cloud_coverage=json['clouds']['all'],
            visibility=json.get('visibility', None),
            wind_speed=json.get('wind').get('speed'),
            wind_gust=json.get('wind').get('gust'),
            wind_bearing=json.get('wind').get('deg'),
            precipitation_probability=json.get('pop', 0),
            rain=json.get('rain'),
            snow=json.get('snow'),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )

    @staticmethod
    def to_daily_weather_forecast(json):
        return DailyWeatherForecast(
            date_time=datetime.fromtimestamp(json['dt']),
            summary=json['summary'],
            temperature=DataConverter._to_daily_temperature(json['temp']),
            feels_like=DataConverter._to_daily_temperature(json['feels_like']),
            pressure=json['pressure'],
            humidity=json['humidity'],
            dew_point=json.get('dew_point'),
            uv_index=json.get('uvi'),
            cloud_coverage=json['clouds']['all'],
            wind_speed=json.get('wind').get('speed'),
            wind_gust=json.get('wind').get('gust'),
            wind_bearing=json.get('wind').get('deg'),
            precipitation_probability=json.get('pop', 0),
            rain=json.get('rain', 0),
            snow=json.get('snow', 0),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )

    @staticmethod
    def _to_weather_condition(json):
        return WeatherCondition(
            id=json['id'],
            main=json['main'],
            description=json['description'],
            icon=json['icon'],
        )

    @staticmethod
    def _to_daily_temperature(json):
        return DailyTemperature(
            day=json['day'],
            min=json.get('min'),
            max=json.get('max'),
            night=json['night'],
            evening=json['eve'],
            morning=json['morn'],
        )
