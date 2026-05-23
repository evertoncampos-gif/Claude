"""Entry point for the weather SMS alert service."""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
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
    from scheduler import WeatherAlertScheduler

    weather = WeatherClient(
        api_key=_require("OPENWEATHER_API_KEY"),
        city=os.getenv("CITY", "São Paulo,BR"),
        units="metric",
    )

    sms = SMSSender(
        account_sid=_require("TWILIO_ACCOUNT_SID"),
        auth_token=_require("TWILIO_AUTH_TOKEN"),
        from_number=_require("TWILIO_FROM_NUMBER"),
        to_number=_require("TWILIO_TO_NUMBER"),
    )

    scheduler = WeatherAlertScheduler(
        weather=weather,
        sms=sms,
        daily_hour=int(os.getenv("DAILY_SUMMARY_HOUR", "7")),
        daily_minute=int(os.getenv("DAILY_SUMMARY_MINUTE", "0")),
        rain_check_interval_minutes=int(os.getenv("RAIN_CHECK_INTERVAL_MINUTES", "30")),
    )

    logger.info("Starting Weather SMS Alert Service...")
    scheduler.start()


if __name__ == "__main__":
    main()
