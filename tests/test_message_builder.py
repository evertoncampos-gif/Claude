"""Tests for message_builder module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from message_builder import build_daily_summary, build_rain_alert, build_current_weather
from weather_client import WeatherCondition, DailyForecast


def _make_forecast(days_offset: int, has_rain: bool = False) -> DailyForecast:
    from datetime import timedelta
    return DailyForecast(
        date=datetime.now() + timedelta(days=days_offset),
        temp_min=18.0,
        temp_max=28.0,
        description="Céu claro" if not has_rain else "Chuva leve",
        rain_probability=0.7 if has_rain else 0.05,
        rain_mm=5.0 if has_rain else 0.0,
        city="São Paulo",
    )


def _make_condition(has_rain: bool = False) -> WeatherCondition:
    return WeatherCondition(
        temperature=22.5,
        feels_like=21.0,
        humidity=70,
        description="Chuva leve" if has_rain else "Céu claro",
        wind_speed=3.5,
        rain_probability=0.8 if has_rain else 0.0,
        rain_mm=3.0 if has_rain else 0.0,
        timestamp=datetime.now(),
        city="São Paulo",
    )


def test_daily_summary_contains_city():
    forecasts = [_make_forecast(i) for i in range(5)]
    msg = build_daily_summary(forecasts, "São Paulo")
    assert "São Paulo" in msg


def test_daily_summary_shows_rainy_days():
    forecasts = [_make_forecast(0, has_rain=True)] + [_make_forecast(i) for i in range(1, 5)]
    msg = build_daily_summary(forecasts, "São Paulo")
    assert "🌧" in msg
    assert "Hoje" in msg


def test_daily_summary_no_rain_warning_when_clear():
    forecasts = [_make_forecast(i, has_rain=False) for i in range(5)]
    msg = build_daily_summary(forecasts, "São Paulo")
    assert "Dias com chuva" not in msg


def test_rain_alert_contains_severity():
    conditions = [_make_condition(has_rain=True)]
    msg = build_rain_alert(conditions, "São Paulo")
    assert "ALERTA" in msg
    assert "São Paulo" in msg
    assert "%" in msg


def test_rain_alert_empty_when_no_conditions():
    msg = build_rain_alert([], "São Paulo")
    assert msg == ""


def test_current_weather_format():
    cond = _make_condition(has_rain=False)
    msg = build_current_weather(cond)
    assert "°C" in msg
    assert "São Paulo" in msg


def test_weather_condition_has_rain():
    cond_rain = _make_condition(has_rain=True)
    cond_clear = _make_condition(has_rain=False)
    assert cond_rain.has_rain is True
    assert cond_clear.has_rain is False


def test_rain_severity_levels():
    def cond_with(mm: float) -> WeatherCondition:
        c = _make_condition(has_rain=True)
        c.rain_mm = mm
        return c

    assert cond_with(25.0).rain_severity == "forte"
    assert cond_with(8.0).rain_severity == "moderada"
    assert cond_with(1.0).rain_severity == "leve"
