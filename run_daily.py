"""One-shot script: sends daily weather summary via SMS."""

import logging
import os
import sys
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
    from message_builder import build_daily_summary

    weather = WeatherClient(
        api_key=_require("OPENWEATHER_API_KEY"),
        city=os.getenv("CITY", "São Paulo,BR"),
    )
    sms = SMSSender(
        account_sid=_require("TWILIO_ACCOUNT_SID"),
        auth_token=_require("TWILIO_AUTH_TOKEN"),
        from_number=_require("TWILIO_FROM_NUMBER"),
        to_number=_require("TWILIO_TO_NUMBER"),
    )

    forecasts = weather.daily_forecast(days=5)
    city = forecasts[0].city if forecasts else weather.city
    message = build_daily_summary(forecasts, city)
    logger.info("Sending daily summary for %s...", city)
    sms.send(message)
    logger.info("Done.")


if __name__ == "__main__":
    main()
