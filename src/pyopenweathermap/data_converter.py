from datetime import UTC, datetime

from .weather import CurrentWeather, WeatherCondition, MinutelyWeatherForecast, HourlyWeatherForecast, DailyWeatherForecast, DailyTemperature
from .air_pollution import CurrentAirPollution


class DataConverter:
    @staticmethod
    def onecall_to_current_weather(json):
        return CurrentWeather(
            date_time=datetime.fromtimestamp(json['dt'], tz=UTC),
            temperature=json['temp'],
            feels_like=json['feels_like'],
            pressure=json['pressure'],
            humidity=json['humidity'],
            dew_point=json['dew_point'],
            uv_index=json['uvi'],
            cloud_coverage=json['clouds'],
            visibility=json.get('visibility'),
            wind_speed=json['wind_speed'],
            wind_gust=json.get('wind_gust'),
            wind_bearing=json['wind_deg'],
            rain=json.get('rain'),
            snow=json.get('snow'),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )
    
    @staticmethod
    def onecall_to_minutely_weather_forecast(json):
        return MinutelyWeatherForecast(
            date_time=datetime.fromtimestamp(json['dt'], tz=UTC),
            precipitation=json.get('precipitation'),
        )

    @staticmethod
    def onecall_to_hourly_weather_forecast(json):
        return HourlyWeatherForecast(
            date_time=datetime.fromtimestamp(json['dt'], tz=UTC),
            temperature=json['temp'],
            feels_like=json['feels_like'],
            pressure=json['pressure'],
            humidity=json['humidity'],
            dew_point=json['dew_point'],
            uv_index=json['uvi'],
            cloud_coverage=json['clouds'],
            visibility=json.get('visibility'),
            wind_speed=json['wind_speed'],
            wind_gust=json.get('wind_gust'),
            wind_bearing=json['wind_deg'],
            precipitation_probability=json.get('pop', 0),
            rain=json.get('rain'),
            snow=json.get('snow'),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )

    @staticmethod
    def onecall_to_daily_weather_forecast(json):
        return DailyWeatherForecast(
            date_time=datetime.fromtimestamp(json['dt'], tz=UTC),
            summary=json.get('summary'),
            temperature=DataConverter._to_daily_temperature(json['temp']),
            feels_like=DataConverter._to_daily_temperature(json['feels_like']),
            pressure=json['pressure'],
            humidity=json['humidity'],
            dew_point=json['dew_point'],
            uv_index=json['uvi'],
            cloud_coverage=json['clouds'],
            wind_speed=json['wind_speed'],
            wind_gust=json.get('wind_gust'),
            wind_bearing=json['wind_deg'],
            precipitation_probability=json.get('pop', 0),
            rain=json.get('rain', 0),
            snow=json.get('snow', 0),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )

    @staticmethod
    def air_pollution_current(json):
        data = json['list'][0]
        components = data['components']
        return CurrentAirPollution(
            date_time=datetime.fromtimestamp(data["dt"], tz=UTC),
            aqi=data['main']['aqi'],
            co=components['co'],
            no=components['no'],
            no2=components['no2'],
            o3=components['o3'],
            so2=components['so2'],
            pm2_5=components['pm2_5'],
            pm10=components['pm10'],
            nh3=components['nh3'],
        )

    @staticmethod
    def air_pollution_hourly(json):
        components = json['components']
        return CurrentAirPollution(
            date_time=datetime.fromtimestamp(json["dt"], tz=UTC),
            aqi=json['main']['aqi'],
            co=components['co'],
            no=components['no'],
            no2=components['no2'],
            o3=components['o3'],
            so2=components['so2'],
            pm2_5=components['pm2_5'],
            pm10=components['pm10'],
            nh3=components['nh3'],
        )

    @staticmethod
    def free_to_current_weather(json):
        return CurrentWeather(
            date_time=datetime.fromtimestamp(json['dt'], tz=UTC),
            temperature=json['main']['temp'],
            feels_like=json['main']['feels_like'],
            pressure=json['main']['pressure'],
            humidity=json['main']['humidity'],
            dew_point=None,
            uv_index=None,
            cloud_coverage=json['clouds']['all'],
            visibility=json.get('visibility'),
            wind_speed=json['wind']['speed'],
            wind_gust=json['wind'].get('gust'),
            wind_bearing=json['wind']['deg'],
            rain=json.get('rain'),
            snow=json.get('snow'),
            condition=DataConverter._to_weather_condition(json['weather'][0]),
        )
        
    @staticmethod
    def free_to_hourly_weather_forecast(json):
        return HourlyWeatherForecast(
            date_time=datetime.fromtimestamp(json['dt'], tz=UTC),
            temperature=json['main']['temp'],
            feels_like=json['main']['feels_like'],
            pressure=json['main']['pressure'],
            humidity=json['main']['humidity'],
            dew_point=None,
            uv_index=None,
            cloud_coverage=json['clouds']['all'],
            visibility=json.get('visibility'),
            wind_speed=json['wind']['speed'],
            wind_gust=json['wind'].get('gust'),
            wind_bearing=json['wind']['deg'],
            precipitation_probability=json.get('pop', 0),
            rain=json.get('rain'),
            snow=json.get('snow'),
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
