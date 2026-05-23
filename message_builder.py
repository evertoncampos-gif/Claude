"""Builds human-readable SMS messages from weather data."""

from datetime import datetime
from weather_client import WeatherCondition, DailyForecast


DAYS_PT = {
    0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
    4: "Sexta", 5: "Sábado", 6: "Domingo",
}

MONTHS_PT = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
}


def _day_label(dt: datetime) -> str:
    today = datetime.now().date()
    if dt.date() == today:
        return "Hoje"
    if (dt.date() - today).days == 1:
        return "Amanhã"
    return f"{DAYS_PT[dt.weekday()]} {dt.day}/{MONTHS_PT[dt.month]}"


def build_daily_summary(forecasts: list[DailyForecast], city: str) -> str:
    now = datetime.now().strftime("%d/%m %H:%M")
    lines = [f"☀️ Previsão do tempo - {city}", f"📅 {now}", ""]

    for f in forecasts[:5]:
        label = _day_label(f.date)
        rain_info = ""
        if f.has_rain:
            rain_info = f"  🌧 Chuva {int(f.rain_probability * 100)}%"
            if f.rain_mm > 0:
                rain_info += f" ({f.rain_mm:.1f}mm)"

        lines.append(
            f"{label}: {f.temp_min:.0f}°-{f.temp_max:.0f}°C"
            f"  {f.description}{rain_info}"
        )

    rainy_days = [f for f in forecasts[:5] if f.has_rain]
    if rainy_days:
        lines.append("")
        lines.append("⚠️ Dias com chuva prevista: " + ", ".join(_day_label(f.date) for f in rainy_days))

    return "\n".join(lines)


def build_rain_alert(conditions: list[WeatherCondition], city: str) -> str:
    if not conditions:
        return ""

    first = conditions[0]
    time_str = first.timestamp.strftime("%H:%M")

    severity = first.rain_severity
    emoji = "⛈️" if severity == "forte" else "🌧️" if severity == "moderada" else "🌦️"

    lines = [
        f"{emoji} ALERTA DE CHUVA - {city}",
        f"Chuva {severity} prevista a partir das {time_str}.",
        f"Probabilidade: {int(first.rain_probability * 100)}%",
    ]

    if first.rain_mm > 0:
        lines.append(f"Volume estimado: {first.rain_mm:.1f}mm")

    lines.append(f"Temp. atual: {first.temperature:.0f}°C ({first.description.lower()})")

    if len(conditions) > 1:
        last = conditions[-1]
        lines.append(f"Duração prevista: até {last.timestamp.strftime('%H:%M')}")

    return "\n".join(lines)


def build_current_weather(cond: WeatherCondition) -> str:
    lines = [
        f"🌡️ Tempo agora em {cond.city}",
        f"{cond.temperature:.0f}°C (sensação {cond.feels_like:.0f}°C)",
        f"{cond.description}",
        f"Umidade: {cond.humidity}%  Vento: {cond.wind_speed:.1f}m/s",
    ]
    if cond.has_rain:
        lines.append(f"🌧 Chuva: {cond.rain_mm:.1f}mm")
    return "\n".join(lines)
