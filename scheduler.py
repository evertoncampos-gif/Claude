"""Scheduler: daily summary + immediate rain alerts."""

import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from message_builder import build_daily_summary, build_rain_alert
from sms_sender import SMSSender
from weather_client import WeatherClient, WeatherCondition

logger = logging.getLogger(__name__)


class WeatherAlertScheduler:
    def __init__(
        self,
        weather: WeatherClient,
        sms: SMSSender,
        daily_hour: int = 7,
        daily_minute: int = 0,
        rain_check_interval_minutes: int = 30,
    ):
        self.weather = weather
        self.sms = sms
        self.daily_hour = daily_hour
        self.daily_minute = daily_minute
        self.rain_check_interval = rain_check_interval_minutes
        self._last_rain_alert: datetime | None = None
        self._rain_alert_cooldown_minutes = 60
        self._scheduler = BlockingScheduler(timezone="America/Sao_Paulo")

    def _send_daily_summary(self) -> None:
        logger.info("Sending daily summary...")
        try:
            forecasts = self.weather.daily_forecast(days=5)
            city = forecasts[0].city if forecasts else self.weather.city
            message = build_daily_summary(forecasts, city)
            self.sms.send(message)
        except Exception as exc:
            logger.error("Daily summary failed: %s", exc)

    def _check_rain(self) -> None:
        logger.debug("Checking for rain...")
        try:
            rain_windows = self.weather.next_rain_windows()
            if not rain_windows:
                return

            now = datetime.now()
            if self._last_rain_alert:
                elapsed = (now - self._last_rain_alert).total_seconds() / 60
                if elapsed < self._rain_alert_cooldown_minutes:
                    logger.debug("Rain alert on cooldown (%dm remaining)", self._rain_alert_cooldown_minutes - elapsed)
                    return

            current = self.weather.current_weather()
            city = current.city

            # Only alert if rain is coming within the next 3 hours
            near_term = [
                w for w in rain_windows
                if (w.timestamp - now) <= timedelta(hours=3)
            ]
            if not near_term:
                return

            message = build_rain_alert(near_term, city)
            if message and self.sms.send(message):
                self._last_rain_alert = now
                logger.info("Rain alert sent for %s", city)

        except Exception as exc:
            logger.error("Rain check failed: %s", exc)

    def start(self) -> None:
        self._scheduler.add_job(
            self._send_daily_summary,
            CronTrigger(hour=self.daily_hour, minute=self.daily_minute),
            id="daily_summary",
            name="Daily weather summary",
        )
        self._scheduler.add_job(
            self._check_rain,
            IntervalTrigger(minutes=self.rain_check_interval),
            id="rain_check",
            name="Rain alert check",
        )

        logger.info(
            "Scheduler started — daily at %02d:%02d, rain check every %dm",
            self.daily_hour,
            self.daily_minute,
            self.rain_check_interval,
        )

        # Fire daily summary immediately on first run
        self._send_daily_summary()
        self._check_rain()

        self._scheduler.start()
