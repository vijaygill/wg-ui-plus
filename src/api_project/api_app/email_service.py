"""SMTP configuration, validation, and safe email delivery helpers."""

import base64
import binascii
import logging
import os
import smtplib
import socket
import ssl
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email

logger = logging.getLogger(__name__)

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}
SMTP_REQUIRED = ("EMAIL_HOST", "EMAIL_PORT", "EMAIL_DEFAULT_FROM_EMAIL")

EMAIL_DELIVERY_GENERIC_MESSAGE = (
    "Email delivery failed. Check the SMTP settings, then check the server logs for more details."
)
EMAIL_DELIVERY_AUTHENTICATION_MESSAGE = (
    "Email authentication failed. Check the SMTP username/app password, then check the server logs for more details."
)
EMAIL_DELIVERY_CONNECTION_MESSAGE = (
    "The email server could not be reached. Check the SMTP host/port and network, then check the server logs for more details."
)
EMAIL_DELIVERY_SECURITY_MESSAGE = (
    "Email security negotiation failed. Check the SMTP TLS/SSL settings and certificate, then check the server logs for more details."
)


class EmailConfigurationError(Exception):
    """SMTP is absent or cannot be used."""


class EmailRecipientError(Exception):
    """The peer has no valid saved recipient."""


class EmailDeliveryError(Exception):
    """The SMTP backend rejected or could not deliver a message."""


@dataclass(frozen=True)
class SMTPConfiguration:
    host: str
    username: str
    password: str
    port: int
    use_ssl: bool
    use_tls: bool
    from_email: str


def parse_boolean(value, name):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ImproperlyConfigured(f"{name} must be true/1/yes/on or false/0/no/off.")


def parse_smtp_configuration(environ=None, *, require_complete=True):
    environ = os.environ if environ is None else environ
    if not require_complete:
        try:
            return parse_smtp_configuration(environ, require_complete=True)
        except ImproperlyConfigured:
            return None

    values = {name: environ.get(name, "") for name in SMTP_REQUIRED}
    missing = [name for name, value in values.items() if not str(value).strip()]
    if missing:
        raise ImproperlyConfigured("Missing SMTP settings: " + ", ".join(missing))
    try:
        port = int(str(values["EMAIL_PORT"]).strip())
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured("EMAIL_PORT must be an integer.") from exc
    if not 1 <= port <= 65535:
        raise ImproperlyConfigured("EMAIL_PORT must be between 1 and 65535.")

    username = str(environ.get("EMAIL_HOST_USER", "")).strip()
    password = environ.get("EMAIL_HOST_PASSWORD", "")
    if bool(username) != bool(str(password).strip()):
        raise ImproperlyConfigured(
            "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be supplied together."
        )

    use_ssl = parse_boolean(environ.get("EMAIL_USE_SSL", "false"), "EMAIL_USE_SSL")
    use_tls = parse_boolean(environ.get("EMAIL_USE_TLS", "false"), "EMAIL_USE_TLS")
    if use_ssl and use_tls:
        raise ImproperlyConfigured("EMAIL_USE_SSL and EMAIL_USE_TLS cannot both be enabled.")

    from_email = str(values["EMAIL_DEFAULT_FROM_EMAIL"]).strip()
    try:
        validate_email(from_email)
    except ValidationError as exc:
        raise ImproperlyConfigured("EMAIL_DEFAULT_FROM_EMAIL must be a valid email address.") from exc

    return SMTPConfiguration(
        host=str(values["EMAIL_HOST"]).strip(), username=username,
        password=password, port=port, use_ssl=use_ssl, use_tls=use_tls,
        from_email=from_email,
    )


def get_email_status():
    """Return safe capability information without exposing SMTP credentials."""
    configured_names = SMTP_REQUIRED + (
        "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "EMAIL_USE_TLS", "EMAIL_USE_SSL",
    )
    if not any(str(os.environ.get(name, "")).strip() for name in configured_names):
        return {
            "status": "unavailable",
            "message": "SMTP email is not configured. Set EMAIL_HOST, EMAIL_PORT, and EMAIL_DEFAULT_FROM_EMAIL.",
        }
    try:
        parse_smtp_configuration(require_complete=True)
    except ImproperlyConfigured as exc:
        return {"status": "invalid", "message": str(exc)}
    return {"status": "configured", "message": "SMTP email is configured."}


def validate_recipient(recipient):
    if not isinstance(recipient, str) or not recipient.strip():
        raise EmailRecipientError("The peer does not have an email address configured.")
    recipient = recipient.strip()
    try:
        validate_email(recipient)
    except ValidationError as exc:
        raise EmailRecipientError("The peer email address is invalid.") from exc
    return recipient


def _validated_configuration():
    try:
        return parse_smtp_configuration()
    except ImproperlyConfigured as exc:
        raise EmailConfigurationError(str(exc)) from exc


def _delivery_failure_message(exc):
    """Map SMTP failures to safe UI messages without provider details."""
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return "authentication", EMAIL_DELIVERY_AUTHENTICATION_MESSAGE
    if isinstance(exc, (ssl.SSLError, ssl.CertificateError)):
        return "security_negotiation", EMAIL_DELIVERY_SECURITY_MESSAGE
    if isinstance(exc, (
        smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, socket.timeout,
        socket.gaierror, socket.herror, TimeoutError, ConnectionError,
    )) or (isinstance(exc, OSError) and not isinstance(exc, smtplib.SMTPException)):
        return "connection", EMAIL_DELIVERY_CONNECTION_MESSAGE
    return "delivery", EMAIL_DELIVERY_GENERIC_MESSAGE


def _send_email(subject, body, recipient, *, attachments=None, operation="email"):
    smtp = _validated_configuration()
    try:
        email = EmailMessage(subject=subject, body=body, from_email=smtp.from_email, to=[recipient])
        for attachment in attachments or ():
            email.attach(*attachment)
        email.send(fail_silently=False)
    except Exception as exc:
        category, message = _delivery_failure_message(exc)
        logger.error(
            "Email delivery failed",
            extra={
                "operation": operation,
                "failure_category": category,
                "exception_type": type(exc).__name__,
                "smtp_host": smtp.host,
                "smtp_port": smtp.port,
            },
        )
        raise EmailDeliveryError(message) from exc


def send_configuration_email(subject, body, recipient, qr, configuration):
    """Send validated peer text and PNG attachments."""
    recipient = validate_recipient(recipient)
    if not isinstance(configuration, str) or not configuration.strip():
        raise EmailDeliveryError("The peer configuration could not be generated.")
    try:
        qr_bytes = base64.b64decode(qr, validate=True)
        if not qr_bytes:
            raise ValueError
    except (binascii.Error, TypeError, ValueError) as exc:
        raise EmailDeliveryError("The peer QR image could not be generated.") from exc
    _send_email(
        subject, body, recipient,
        attachments=(
            ("tunnel.conf", configuration, "text/plain"),
            ("tunnel.png", qr_bytes, "image/png"),
        ),
        operation="peer_configuration",
    )


def send_test_email():
    """Send a content-only test message from the configured address to itself."""
    smtp = _validated_configuration()
    _send_email(
        "wg-ui-plus SMTP test email",
        "This is a test email from wg-ui-plus.",
        smtp.from_email,
        operation="test",
    )


def email_peer_configuration(peer):
    from .serializers import PeerWithQrSerializer

    recipient = validate_recipient(peer.email_address)
    generated = PeerWithQrSerializer(peer).data
    send_configuration_email(
        f"Tunnel configuration sent from wg-ui-plus for {peer.name}",
        f"The WireGuard configuration for {peer.name} is attached. Keep it safe.",
        recipient, generated["qr"], generated["configuration"],
    )
