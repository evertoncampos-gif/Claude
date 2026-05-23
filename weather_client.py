"""Weather data client using OpenWeatherMap API."""

import os
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
