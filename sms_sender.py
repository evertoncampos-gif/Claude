"""SMS sender using Twilio."""

import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)


class SMSSender:
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number

    def send(self, message: str) -> bool:
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number,
            )
            logger.info("SMS sent: %s (sid=%s)", msg.status, msg.sid)
            return True
        except Exception as exc:
            logger.error("Failed to send SMS: %s", exc)
            return False
