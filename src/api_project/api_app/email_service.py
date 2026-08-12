"""SMTP configuration, validation, and peer-configuration delivery."""

import base64
import binascii
import logging
import os
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email

logger = logging.getLogger(__name__)

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}
SMTP_REQUIRED = ("EMAIL_HOST", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "EMAIL_PORT")


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
    use_ssl = parse_boolean(environ.get("EMAIL_USE_SSL", "false"), "EMAIL_USE_SSL")
    use_tls = parse_boolean(environ.get("EMAIL_USE_TLS", "false"), "EMAIL_USE_TLS")
    if use_ssl and use_tls:
        raise ImproperlyConfigured("EMAIL_USE_SSL and EMAIL_USE_TLS cannot both be enabled.")
    if not (use_ssl or use_tls):
        raise ImproperlyConfigured("Enable exactly one SMTP transport security mode.")
    from_email = environ.get("EMAIL_DEFAULT_FROM_EMAIL") or values["EMAIL_HOST_USER"]
    try:
        validate_email(from_email.strip())
    except ValidationError as exc:
        raise ImproperlyConfigured(
            "EMAIL_DEFAULT_FROM_EMAIL or EMAIL_HOST_USER must be a valid email address."
        ) from exc
    return SMTPConfiguration(
        host=values["EMAIL_HOST"].strip(), username=values["EMAIL_HOST_USER"].strip(),
        password=values["EMAIL_HOST_PASSWORD"], port=port, use_ssl=use_ssl,
        use_tls=use_tls, from_email=from_email.strip(),
    )


def get_email_status():
    """Return safe capability information without exposing SMTP credentials."""
    environment_values = [os.environ.get(name, "").strip() for name in SMTP_REQUIRED]
    if not any(environment_values):
        return {"status": "unavailable", "message": "SMTP email is not configured."}
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
        raise EmailConfigurationError("SMTP email is unavailable or incorrectly configured.") from exc


def send_configuration_email(subject, body, recipient, qr, configuration):
    """Send validated text and PNG attachments, translating backend errors safely."""
    smtp = _validated_configuration()
    recipient = validate_recipient(recipient)
    if not isinstance(configuration, str) or not configuration.strip():
        raise EmailDeliveryError("The peer configuration could not be generated.")
    try:
        qr_bytes = base64.b64decode(qr, validate=True)
        if not qr_bytes:
            raise ValueError
    except (binascii.Error, TypeError, ValueError) as exc:
        raise EmailDeliveryError("The peer QR image could not be generated.") from exc
    try:
        email = EmailMessage(subject=subject, body=body, from_email=smtp.from_email, to=[recipient])
        email.attach("tunnel.conf", configuration, "text/plain")
        email.attach("tunnel.png", qr_bytes, "image/png")
        email.send(fail_silently=False)
    except Exception as exc:
        logger.exception("Peer configuration email delivery failed", extra={"smtp_host": smtp.host, "smtp_port": smtp.port})
        raise EmailDeliveryError("The email could not be delivered.") from exc


def email_peer_configuration(peer):
    from .serializers import PeerWithQrSerializer

    recipient = validate_recipient(peer.email_address)
    generated = PeerWithQrSerializer(peer).data
    send_configuration_email(
        f"Tunnel configuration sent from wg-ui-plus for {peer.name}",
        f"The WireGuard configuration for {peer.name} is attached. Keep it safe.",
        recipient, generated["qr"], generated["configuration"],
    )
