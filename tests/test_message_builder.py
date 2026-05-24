"""Tests for message_builder module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from message_builder import (
    build_daily_summary,
    build_rain_alert,
    build_current_weather,
    build_air_quality_alert,
    build_conditions_alert,
)
from weather_client import WeatherCondition, DailyForecast, AirQualityData, CurrentConditions


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
    assert "Sao Paulo" in msg


def test_daily_summary_shows_rainy_days():
    forecasts = [_make_forecast(0, has_rain=True)] + [_make_forecast(i) for i in range(1, 5)]
    msg = build_daily_summary(forecasts, "São Paulo")
    assert "C70%" in msg
    assert "Hoje" in msg


def test_daily_summary_no_rain_warning_when_clear():
    forecasts = [_make_forecast(i, has_rain=False) for i in range(5)]
    msg = build_daily_summary(forecasts, "São Paulo")
    assert "Dias com chuva" not in msg


def test_rain_alert_contains_severity():
    conditions = [_make_condition(has_rain=True)]
    msg = build_rain_alert(conditions, "São Paulo")
    assert "CHUVA" in msg
    assert "Sao Paulo" in msg
    assert "%" in msg


def test_rain_alert_empty_when_no_conditions():
    msg = build_rain_alert([], "São Paulo")
    assert msg == ""


def test_current_weather_format():
    cond = _make_condition(has_rain=False)
    msg = build_current_weather(cond)
    assert "C" in msg
    assert "Sao Paulo" in msg


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


# --- Helpers for new data classes ---

def _make_air_quality(aqi: int = 4) -> AirQualityData:
    return AirQualityData(
        aqi=aqi,
        pm2_5=35.2,
        pm10=55.0,
        no2=20.1,
        o3=80.5,
        co=500.0,
        timestamp=datetime.now(),
        city="Sao Paulo",
    )


def _make_current_conditions(
    wind_speed: float = 5.0,
    temperature: float = 25.0,
    humidity: int = 60,
    visibility: int = 5000,
) -> CurrentConditions:
    return CurrentConditions(
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        visibility=visibility,
        pressure=1013.0,
        description="Ceu claro",
        city="Sao Paulo",
        timestamp=datetime.now(),
    )


# --- AirQualityData property tests ---

def test_air_quality_label_values():
    assert _make_air_quality(1).label == "Boa"
    assert _make_air_quality(2).label == "Razoavel"
    assert _make_air_quality(3).label == "Moderada"
    assert _make_air_quality(4).label == "Ruim"
    assert _make_air_quality(5).label == "Muito ruim"


def test_air_quality_is_concerning_threshold():
    assert _make_air_quality(1).is_concerning is False
    assert _make_air_quality(2).is_concerning is False
    assert _make_air_quality(3).is_concerning is True
    assert _make_air_quality(5).is_concerning is True


# --- CurrentConditions property tests ---

def test_has_strong_wind():
    assert _make_current_conditions(wind_speed=17.0).has_strong_wind is True
    assert _make_current_conditions(wind_speed=16.9).has_strong_wind is False


def test_has_extreme_heat():
    assert _make_current_conditions(temperature=38.0).has_extreme_heat is True
    assert _make_current_conditions(temperature=37.9).has_extreme_heat is False


def test_has_low_humidity():
    assert _make_current_conditions(humidity=30).has_low_humidity is True
    assert _make_current_conditions(humidity=31).has_low_humidity is False


def test_has_low_visibility():
    assert _make_current_conditions(visibility=1000).has_low_visibility is True
    assert _make_current_conditions(visibility=1001).has_low_visibility is False


# --- build_air_quality_alert tests ---

def test_air_quality_alert_contains_city():
    aq = _make_air_quality(4)
    msg = build_air_quality_alert(aq)
    assert "Sao Paulo" in msg


def test_air_quality_alert_contains_label():
    aq = _make_air_quality(4)
    msg = build_air_quality_alert(aq)
    assert "Ruim" in msg


def test_air_quality_alert_contains_aqi_level():
    aq = _make_air_quality(5)
    msg = build_air_quality_alert(aq)
    assert "5" in msg


def test_air_quality_alert_max_160_chars():
    aq = _make_air_quality(4)
    msg = build_air_quality_alert(aq)
    assert len(msg) <= 160


def test_air_quality_alert_no_accents():
    aq = AirQualityData(
        aqi=5,
        pm2_5=99.9,
        pm10=120.0,
        no2=50.0,
        o3=100.0,
        co=1000.0,
        timestamp=datetime.now(),
        city="Sao Paulo",
    )
    msg = build_air_quality_alert(aq)
    import unicodedata
    for ch in msg:
        assert unicodedata.category(ch) != "Mn", f"Accent found: {ch!r}"


# --- build_conditions_alert tests ---

def test_conditions_alert_contains_city():
    cond = _make_current_conditions(wind_speed=20.0)
    msg = build_conditions_alert(cond, ["Vento forte"])
    assert "Sao Paulo" in msg


def test_conditions_alert_contains_trigger():
    cond = _make_current_conditions(wind_speed=20.0)
    msg = build_conditions_alert(cond, ["Vento forte"])
    assert "Vento forte" in msg


def test_conditions_alert_multiple_triggers():
    cond = _make_current_conditions(wind_speed=20.0, temperature=39.0)
    msg = build_conditions_alert(cond, ["Vento forte", "Calor extremo"])
    assert "Vento forte" in msg
    assert "Calor extremo" in msg


def test_conditions_alert_max_160_chars():
    cond = _make_current_conditions(wind_speed=20.0, temperature=40.0, humidity=20, visibility=500)
    msg = build_conditions_alert(cond, ["Vento forte", "Calor extremo", "Umidade baixa", "Visibilidade baixa"])
    assert len(msg) <= 160


def test_conditions_alert_no_accents():
    cond = CurrentConditions(
        temperature=40.0,
        humidity=20,
        wind_speed=20.0,
        visibility=500,
        pressure=1010.0,
        description="Ceu limpo",
        city="Sao Paulo",
        timestamp=datetime.now(),
    )
    msg = build_conditions_alert(cond, ["Vento forte"])
    import unicodedata
    for ch in msg:
        assert unicodedata.category(ch) != "Mn", f"Accent found: {ch!r}"
