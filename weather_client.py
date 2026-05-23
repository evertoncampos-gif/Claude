"""Weather data client using OpenWeatherMap API."""

import os
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, ClassVar


@dataclass
class WeatherCondition:
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    rain_probability: float
    rain_mm: float
    timestamp: datetime
    city: str

    @property
    def has_rain(self) -> bool:
        return self.rain_probability >= 0.3 or self.rain_mm > 0

    @property
    def rain_severity(self) -> str:
        if self.rain_mm >= 20:
            return "forte"
        if self.rain_mm >= 5:
            return "moderada"
        if self.rain_mm > 0 or self.rain_probability >= 0.3:
            return "leve"
        return "sem chuva"


@dataclass
class DailyForecast:
    date: datetime
    temp_min: float
    temp_max: float
    description: str
    rain_probability: float
    rain_mm: float
    city: str

    @property
    def has_rain(self) -> bool:
        return self.rain_probability >= 0.3 or self.rain_mm > 0


class WeatherClient:
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str, city: str, units: str = "metric"):
        self.api_key = api_key
        self.city = city
        self.units = units

    def _get(self, endpoint: str, params: dict) -> dict:
        params.update({"appid": self.api_key, "units": self.units, "lang": "pt_br"})
        response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def current_weather(self) -> WeatherCondition:
        data = self._get("weather", {"q": self.city})
        rain = data.get("rain", {})
        return WeatherCondition(
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"].capitalize(),
            wind_speed=data["wind"]["speed"],
            rain_probability=0.0,
            rain_mm=rain.get("1h", rain.get("3h", 0.0)),
            timestamp=datetime.fromtimestamp(data["dt"]),
            city=data["name"],
        )

    def hourly_forecast(self) -> list[WeatherCondition]:
        data = self._get("forecast", {"q": self.city, "cnt": 8})
        results = []
        for item in data["list"]:
            rain = item.get("rain", {})
            results.append(WeatherCondition(
                temperature=item["main"]["temp"],
                feels_like=item["main"]["feels_like"],
                humidity=item["main"]["humidity"],
                description=item["weather"][0]["description"].capitalize(),
                wind_speed=item["wind"]["speed"],
                rain_probability=item.get("pop", 0.0),
                rain_mm=rain.get("3h", 0.0),
                timestamp=datetime.fromtimestamp(item["dt"]),
                city=data["city"]["name"],
            ))
        return results

    def daily_forecast(self, days: int = 5) -> list[DailyForecast]:
        """Returns daily forecast by aggregating 3-hour intervals."""
        data = self._get("forecast", {"q": self.city, "cnt": days * 8})
        city_name = data["city"]["name"]

        days_map: dict[str, dict] = {}
        for item in data["list"]:
            day_key = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            rain = item.get("rain", {})
            rain_mm = rain.get("3h", 0.0)
            pop = item.get("pop", 0.0)

            if day_key not in days_map:
                days_map[day_key] = {
                    "temps": [],
                    "descriptions": [],
                    "rain_probs": [],
                    "rain_mm": 0.0,
                    "dt": item["dt"],
                }

            days_map[day_key]["temps"].append(item["main"]["temp"])
            days_map[day_key]["descriptions"].append(item["weather"][0]["description"])
            days_map[day_key]["rain_probs"].append(pop)
            days_map[day_key]["rain_mm"] += rain_mm

        forecasts = []
        for day_key, d in sorted(days_map.items()):
            forecasts.append(DailyForecast(
                date=datetime.strptime(day_key, "%Y-%m-%d"),
                temp_min=min(d["temps"]),
                temp_max=max(d["temps"]),
                description=max(set(d["descriptions"]), key=d["descriptions"].count).capitalize(),
                rain_probability=max(d["rain_probs"]),
                rain_mm=d["rain_mm"],
                city=city_name,
            ))
        return forecasts

    def next_rain_windows(self) -> list[WeatherCondition]:
        """Returns upcoming hours where rain is expected."""
        return [h for h in self.hourly_forecast() if h.has_rain]

    def _get_coords(self) -> tuple[float, float]:
        """Returns (lat, lon) for the configured city."""
        data = self._get("weather", {"q": self.city})
        return data["coord"]["lat"], data["coord"]["lon"]

    def air_quality(self) -> "AirQualityData":
        """Fetches current air quality using the /air_pollution endpoint."""
        lat, lon = self._get_coords()
        params = {"lat": lat, "lon": lon, "appid": self.api_key}
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/air_pollution",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        item = data["list"][0]
        components = item["components"]
        return AirQualityData(
            aqi=item["main"]["aqi"],
            pm2_5=components.get("pm2_5", 0.0),
            pm10=components.get("pm10", 0.0),
            no2=components.get("no2", 0.0),
            o3=components.get("o3", 0.0),
            co=components.get("co", 0.0),
            timestamp=datetime.fromtimestamp(item["dt"]),
            city=self.city,
        )

    def current_conditions(self) -> "CurrentConditions":
        """Returns current weather conditions."""
        data = self._get("weather", {"q": self.city})
        return CurrentConditions(
            temperature=data["main"]["temp"],
            humidity=data["main"]["humidity"],
            wind_speed=data["wind"]["speed"],
            visibility=data.get("visibility", 10000),
            pressure=data["main"]["pressure"],
            description=data["weather"][0]["description"].capitalize(),
            city=data["name"],
            timestamp=datetime.fromtimestamp(data["dt"]),
        )


@dataclass
class AirQualityData:
    aqi: int  # 1-5 scale
    pm2_5: float
    pm10: float
    no2: float
    o3: float
    co: float
    timestamp: datetime
    city: str

    _AQI_LABELS: ClassVar[dict[int, str]] = {
        1: "Boa",
        2: "Razoavel",
        3: "Moderada",
        4: "Ruim",
        5: "Muito ruim",
    }

    @property
    def label(self) -> str:
        return self._AQI_LABELS.get(self.aqi, "Desconhecida")

    @property
    def is_concerning(self) -> bool:
        return self.aqi >= 3


@dataclass
class CurrentConditions:
    temperature: float
    humidity: int
    wind_speed: float
    visibility: int
    pressure: float
    description: str
    city: str
    timestamp: datetime

    @property
    def has_strong_wind(self) -> bool:
        return self.wind_speed >= 17

    @property
    def has_extreme_heat(self) -> bool:
        return self.temperature >= 38

    @property
    def has_low_humidity(self) -> bool:
        return self.humidity <= 30

    @property
    def has_low_visibility(self) -> bool:
        return self.visibility <= 1000
