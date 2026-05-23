"""One-shot script: checks for upcoming rain and sends SMS alert if found."""

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
    from message_builder import build_rain_alert

    weather = WeatherClient(
        api_key=_require("OPENWEATHER_API_KEY"),
        city=os.getenv("CITY") or "Sao Paulo,BR",
    )
    sms = SMSSender(
        account_sid=_require("TWILIO_ACCOUNT_SID"),
        auth_token=_require("TWILIO_AUTH_TOKEN"),
        from_number=_require("TWILIO_FROM_NUMBER"),
        to_number=_require("TWILIO_TO_NUMBER"),
    )

    now = datetime.now()
    rain_windows = weather.next_rain_windows()

    # Only alert if rain is starting within the next 3 hours
    near_term = [w for w in rain_windows if (w.timestamp - now) <= timedelta(hours=3)]

    if not near_term:
        logger.info("No rain expected in the next 3 hours. No SMS sent.")
        return

    current = weather.current_weather()
    message = build_rain_alert(near_term, current.city)
    logger.info("Rain detected — sending alert for %s...", current.city)
    sms.send(message)
    logger.info("Done.")


if __name__ == "__main__":
    main()
