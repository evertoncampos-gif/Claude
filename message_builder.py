"""Builds compact SMS messages (max 160 chars, no emojis, no accents) from weather data."""

import unicodedata
from datetime import datetime
from weather_client import WeatherCondition, DailyForecast, AirQualityData, CurrentConditions


DAYS_PT = {
    0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui",
    4: "Sex", 5: "Sab", 6: "Dom",
}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _day_label(dt: datetime) -> str:
    today = datetime.now().date()
    diff = (dt.date() - today).days
    if diff == 0:
        return "Hoje"
    if diff == 1:
        return "Amanha"
    return f"{DAYS_PT[dt.weekday()]} {dt.day}/{dt.month:02d}"


def build_daily_summary(forecasts: list[DailyForecast], city: str) -> str:
    lines = [f"Tempo {_strip_accents(city)} {datetime.now().strftime('%d/%m')}:"]
    for f in forecasts[:5]:
        label = _day_label(f.date)
        rain = f" C{int(f.rain_probability * 100)}%" if f.has_rain else ""
        line = f"{label}: {f.temp_min:.0f}-{f.temp_max:.0f}C{rain}"
        if len("\n".join(lines + [line])) <= 160:
            lines.append(line)
        else:
            break
    return "\n".join(lines)


def build_rain_alert(conditions: list[WeatherCondition], city: str) -> str:
    if not conditions:
        return ""
    first = conditions[0]
    last = conditions[-1]
    duration = f" ate {last.timestamp.strftime('%H:%M')}" if len(conditions) > 1 else ""
    severity = _strip_accents(first.rain_severity)
    lines = [
        f"CHUVA em {_strip_accents(city)}!",
        f"Chuva {severity} a partir das {first.timestamp.strftime('%H:%M')}{duration}",
        f"Prob: {int(first.rain_probability * 100)}%",
        f"Temp: {first.temperature:.0f}C",
    ]
    if first.rain_mm > 0:
        lines.append(f"Vol: {first.rain_mm:.1f}mm")
    return "\n".join(lines)


def build_current_weather(cond: WeatherCondition) -> str:
    lines = [
        f"Tempo agora em {_strip_accents(cond.city)}:",
        f"{cond.temperature:.0f}C (sens. {cond.feels_like:.0f}C)",
        f"{_strip_accents(cond.description)}",
        f"Umidade: {cond.humidity}% Vento: {cond.wind_speed:.1f}m/s",
    ]
    if cond.has_rain:
        lines.append(f"Chuva: {cond.rain_mm:.1f}mm")
    return "\n".join(lines)


def build_air_quality_alert(aq: AirQualityData) -> str:
    """Builds an air quality alert SMS (max 160 chars, no accents, no emojis)."""
    city = _strip_accents(aq.city)
    label = _strip_accents(aq.label)
    lines = [
        f"QUALIDADE DO AR em {city}:",
        f"Nivel: {label} (AQI {aq.aqi}/5)",
        f"PM2.5: {aq.pm2_5:.1f} PM10: {aq.pm10:.1f}",
        f"NO2: {aq.no2:.1f} O3: {aq.o3:.1f}",
    ]
    msg = "\n".join(lines)
    return msg[:160]


def build_conditions_alert(cond: CurrentConditions, triggers: list[str]) -> str:
    """Builds a consolidated alert SMS for non-rain weather hazards (max 160 chars)."""
    city = _strip_accents(cond.city)
    desc = _strip_accents(cond.description)
    trigger_line = ", ".join(_strip_accents(t) for t in triggers)
    lines = [
        f"ALERTA CLIMA {city}:",
        trigger_line,
        f"Temp: {cond.temperature:.0f}C Umid: {cond.humidity}%",
        f"Vento: {cond.wind_speed:.1f}m/s Vis: {cond.visibility}m",
        desc,
    ]
    msg = "\n".join(lines)
    return msg[:160]
