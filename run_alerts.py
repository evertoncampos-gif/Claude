"""One-shot script: checks ALL weather hazards and sends a consolidated SMS alert."""

import logging
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        logger.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return value


def main() -> None:
    from weather_client import WeatherClient
    from sms_sender import SMSSender
    from message_builder import build_rain_alert, build_conditions_alert, build_air_quality_alert

    weather = WeatherClient(
        api_key=_require("OPENWEATHER_API_KEY"),
        city=os.getenv("CITY") or "Duque de Caxias,BR",
    )
    sms = SMSSender(
        account_sid=_require("TWILIO_ACCOUNT_SID"),
        auth_token=_require("TWILIO_AUTH_TOKEN"),
        from_number=_require("TWILIO_FROM_NUMBER"),
        to_number=_require("TWILIO_TO_NUMBER"),
    )

    now = datetime.now()
    alerts_sent = False

    # --- Chuva nas proximas 3h ---
    rain_windows = weather.next_rain_windows()
    near_term_rain = [w for w in rain_windows if (w.timestamp - now) <= timedelta(hours=3)]
    if near_term_rain:
        current = weather.current_weather()
        message = build_rain_alert(near_term_rain, current.city)
        logger.info("Rain detected — sending rain alert for %s...", current.city)
        if not sms.send(message):
            logger.error("SMS not delivered (rain alert). Check Twilio credentials.")
            sys.exit(1)
        alerts_sent = True

    # --- Condicoes atmosfericas (vento, calor, umidade, visibilidade) ---
    cond = weather.current_conditions()
    triggers: list[str] = []
    if cond.has_strong_wind:
        triggers.append("Vento forte")
    if cond.has_extreme_heat:
        triggers.append("Calor extremo")
    if cond.has_low_humidity:
        triggers.append("Umidade baixa")
    if cond.has_low_visibility:
        triggers.append("Visibilidade baixa")

    if triggers:
        message = build_conditions_alert(cond, triggers)
        logger.info("Conditions alert (%s) — sending SMS for %s...", triggers, cond.city)
        if not sms.send(message):
            logger.error("SMS not delivered (conditions alert). Check Twilio credentials.")
            sys.exit(1)
        alerts_sent = True

    # --- Qualidade do ar ---
    aq = weather.air_quality()
    if aq.is_concerning:
        message = build_air_quality_alert(aq)
        logger.info("Air quality alert (AQI=%d) — sending SMS for %s...", aq.aqi, aq.city)
        if not sms.send(message):
            logger.error("SMS not delivered (air quality alert). Check Twilio credentials.")
            sys.exit(1)
        alerts_sent = True

    if not alerts_sent:
        logger.info("Sem alertas — no hazardous conditions detected.")


if __name__ == "__main__":
    main()
