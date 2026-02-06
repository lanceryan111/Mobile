#!/usr/bin/env python3
"""SMTP email sender for CI/CD notifications with retry support."""

from __future__ import annotations

import os
import sys
import smtplib
import logging
import time
from email.mime.text import MIMEText
from dataclasses import dataclass, field
from pathlib import Path
from functools import wraps
from typing import Callable, TypeVar, Any, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    retryable_exceptions: Tuple[type, ...] = field(default_factory=lambda: (
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPConnectError,
        smtplib.SMTPHeloError,
        TimeoutError,
        ConnectionError,
    ))


def with_retry(retry_config: RetryConfig) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for adding retry logic with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_config.retryable_exceptions as e:
                    last_exception = e
                    if attempt == retry_config.max_attempts:
                        logger.error(
                            "Attempt %d/%d failed, no more retries: %s",
                            attempt, retry_config.max_attempts, e
                        )
                        raise

                    delay = min(
                        retry_config.base_delay * (retry_config.exponential_base ** (attempt - 1)),
                        retry_config.max_delay
                    )
                    logger.warning(
                        "Attempt %d/%d failed: %s. Retrying in %.1fs...",
                        attempt, retry_config.max_attempts, e, delay
                    )
                    time.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper
    return decorator


@dataclass
class EmailConfig:
    """Email configuration from environment variables."""
    server: str
    port: int
    sender: str
    receivers: List[str]
    subject: str
    body: str
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 10
    retry: RetryConfig = field(default_factory=RetryConfig)

    @classmethod
    def from_env(cls) -> EmailConfig:
        """Load configuration from environment variables."""
        required_vars = ["SMTP_SERVER", "SMTP_PORT", "EMAIL_SENDER", "EMAIL_RECEIVER", "SUBJECT"]
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        # Get body from env or file
        body = os.environ.get("EMAIL_BODY", "")
        body_file = os.environ.get("BODY_FILE")
        if body_file and Path(body_file).exists():
            body = Path(body_file).read_text(encoding="utf-8")
        elif not body:
            raise EnvironmentError("Either EMAIL_BODY or BODY_FILE must be provided")

        receiver_str = os.environ["EMAIL_RECEIVER"]
        receivers = [r.strip() for r in receiver_str.split(",") if r.strip()]

        retry_config = RetryConfig(
            max_attempts=int(os.environ.get("SMTP_MAX_RETRIES", "3")),
            base_delay=float(os.environ.get("SMTP_RETRY_DELAY", "1.0")),
        )

        return cls(
            server=os.environ["SMTP_SERVER"],
            port=int(os.environ["SMTP_PORT"]),
            sender=os.environ["EMAIL_SENDER"],
            receivers=receivers,
            subject=os.environ["SUBJECT"],
            body=body,
            username=os.environ.get("SMTP_USERNAME"),
            password=os.environ.get("SMTP_PASSWORD"),
            timeout=int(os.environ.get("SMTP_TIMEOUT", "10")),
            retry=retry_config,
        )


def build_message(config: EmailConfig) -> MIMEText:
    """Build the email message from config."""
    msg = MIMEText(config.body, "html")
    msg["Subject"] = config.subject
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.receivers)
    return msg


class EmailSender:
    """Email sender with retry support."""

    def __init__(self, config: EmailConfig) -> None:
        self.config = config
        self._send_with_retry = with_retry(config.retry)(self._send_impl)

    def _send_impl(self, msg: MIMEText) -> None:
        """Internal send implementation."""
        logger.info("Connecting to SMTP server %s:%d", self.config.server, self.config.port)

        with smtplib.SMTP(self.config.server, self.config.port, timeout=self.config.timeout) as smtp:
            logger.info("SMTP connected, starting TLS...")
            smtp.starttls()

            if self.config.username and self.config.password:
                logger.info("Authenticating as %s", self.config.username)
                smtp.login(self.config.username, self.config.password)

            logger.info("Sending email to %s", self.config.receivers)
            smtp.sendmail(self.config.sender, self.config.receivers, msg.as_string())

        logger.info("Email sent successfully")

    def send(self, msg: MIMEText) -> None:
        """Send email with retry logic."""
        self._send_with_retry(msg)


def main() -> int:
    """Main entry point."""
    try:
        config = EmailConfig.from_env()
        msg = build_message(config)
        sender = EmailSender(config)
        sender.send(msg)
        return 0
    except EnvironmentError as e:
        logger.error("Configuration error: %s", e)
        return 1
    except FileNotFoundError as e:
        logger.error("File error: %s", e)
        return 1
    except smtplib.SMTPException as e:
        logger.error("SMTP error after all retries: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
