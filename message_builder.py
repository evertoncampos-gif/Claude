"""Builds compact SMS messages (max 160 chars, no emojis) from weather data."""

from datetime import datetime
from weather_client import WeatherCondition, DailyForecast


DAYS_PT = {
    0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui",
    4: "Sex", 5: "Sab", 6: "Dom",
}


def _day_label(dt: datetime) -> str:
    today = datetime.now().date()
    diff = (dt.date() - today).days
    if diff == 0:
        return "Hoje"
    if diff == 1:
        return "Amanha"
    return f"{DAYS_PT[dt.weekday()]} {dt.day}/{dt.month:02d}"


def build_daily_summary(forecasts: list[DailyForecast], city: str) -> str:
    lines = [f"Tempo {city} {datetime.now().strftime('%d/%m')}:"]
    for f in forecasts[:5]:
        label = _day_label(f.date)
        rain = f" Chuva {int(f.rain_probability * 100)}%" if f.has_rain else ""
        lines.append(f"{label}: {f.temp_min:.0f}-{f.temp_max:.0f}C{rain}")
    return "\n".join(lines)


def build_rain_alert(conditions: list[WeatherCondition], city: str) -> str:
    if not conditions:
        return ""
    first = conditions[0]
    last = conditions[-1]
    duration = f" ate {last.timestamp.strftime('%H:%M')}" if len(conditions) > 1 else ""
    lines = [
        f"CHUVA em {city}!",
        f"Chuva {first.rain_severity} a partir das {first.timestamp.strftime('%H:%M')}{duration}",
        f"Prob: {int(first.rain_probability * 100)}%",
        f"Temp: {first.temperature:.0f}C",
    ]
    if first.rain_mm > 0:
        lines.append(f"Vol: {first.rain_mm:.1f}mm")
    return "\n".join(lines)


def build_current_weather(cond: WeatherCondition) -> str:
    lines = [
        f"Tempo agora em {cond.city}:",
        f"{cond.temperature:.0f}C (sens. {cond.feels_like:.0f}C)",
        f"{cond.description}",
        f"Umidade: {cond.humidity}% Vento: {cond.wind_speed:.1f}m/s",
    ]
    if cond.has_rain:
        lines.append(f"Chuva: {cond.rain_mm:.1f}mm")
    return "\n".join(lines)
