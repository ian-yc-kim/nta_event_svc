from __future__ import annotations

import logging
import smtplib
from typing import Callable, Optional
from email.message import EmailMessage

from event_service.core.config import Settings


class EmailSendError(Exception):
    """Raised when sending an email fails."""


class SMTPService:
    """Simple SMTP email sender supporting SSL and STARTTLS.

    The client_factory parameter allows injecting a custom SMTP client for testing.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        client_factory: Optional[Callable[..., smtplib.SMTP | smtplib.SMTP_SSL]] = None,
        timeout: int = 10,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_factory = client_factory
        self.timeout = timeout

    @classmethod
    def from_settings(cls, settings: Settings) -> "SMTPService":
        """Construct SMTPService from application Settings.

        Raises ValueError if required SMTP settings are missing.
        """
        try:
            host = settings.SMTP_HOST
            port = settings.SMTP_PORT
            username = settings.SMTP_USERNAME
            password = settings.SMTP_PASSWORD
        except Exception as e:
            logging.error(e, exc_info=True)
            raise ValueError("Failed reading SMTP settings") from e

        if not (host and port and username and password):
            raise ValueError("Incomplete SMTP settings: SMTP_HOST/SMTP_PORT/SMTP_USERNAME/SMTP_PASSWORD required")

        return cls(host=host, port=port, username=username, password=password)

    def send_email(self, to_emails: list[str], subject: str, body: str, subtype: str = "plain") -> None:
        """Send an email to one or more recipients.

        - Uses STARTTLS when port == 587.
        - Uses SSL (SMTP_SSL) otherwise.
        - Raises EmailSendError on failure with non-sensitive context.
        """
        if not to_emails:
            raise ValueError("to_emails must be a non-empty list of recipient addresses")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.username
        # EmailMessage will accept a list for To if assigned directly, but join for clarity
        msg["To"] = ", ".join(to_emails)
        msg.set_content(body, subtype=subtype)

        # Default factory that returns an SMTP client (context manager)
        def _default_factory(host: str, port: int, timeout: int = 10):
            if port == 587:
                return smtplib.SMTP(host=host, port=port, timeout=timeout)
            return smtplib.SMTP_SSL(host=host, port=port, timeout=timeout)

        factory = self.client_factory or _default_factory

        try:
            # Use context manager form of SMTP/SMTP_SSL
            with factory(self.host, self.port, self.timeout) as smtp:
                if self.port == 587:
                    # STARTTLS flow
                    try:
                        smtp.ehlo()
                        smtp.starttls()
                        smtp.ehlo()
                    except Exception:
                        # If STARTTLS fails, let login/send flow handle and be logged below
                        logging.debug("STARTTLS handshake failed or not supported", exc_info=True)

                # Login and send
                smtp.login(self.username, self.password)
                smtp.send_message(msg)

        except (smtplib.SMTPException, OSError, TimeoutError) as e:
            # Do not log sensitive data such as password
            logging.error(e, exc_info=True)
            raise EmailSendError(
                f"Failed to send email to {to_emails} using SMTP server {self.host}:{self.port} (user={self.username})"
            ) from e
