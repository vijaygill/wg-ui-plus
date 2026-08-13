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
from django.core.mail.backends.smtp import EmailBackend
from django.core.validators import validate_email
from django.db import DatabaseError
from django.test.testcases import DatabaseOperationForbidden

logger = logging.getLogger(__name__)

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}
SMTP_REQUIRED = ("EMAIL_HOST", "EMAIL_PORT", "EMAIL_DEFAULT_FROM_EMAIL")

# Maps ServerConfiguration email model fields to their governing environment
# variable names. Controls in the UI are disabled when the variable is present.
EMAIL_SETTINGS_FIELDS = {
    "email_host": "EMAIL_HOST",
    "email_port": "EMAIL_PORT",
    "email_host_user": "EMAIL_HOST_USER",
    "email_host_password": "EMAIL_HOST_PASSWORD",
    "email_default_from_email": "EMAIL_DEFAULT_FROM_EMAIL",
    "email_use_tls": "EMAIL_USE_TLS",
    "email_use_ssl": "EMAIL_USE_SSL",
}

# Boolean fields follow presence semantics: an explicit environment value of
# "False" still counts as environment-controlled.
EMAIL_SETTINGS_BOOLEAN_FIELDS = {"email_use_tls", "email_use_ssl"}

# Sentinel value the UI sends back to keep the stored password unchanged.
EMAIL_PASSWORD_SENTINEL = "*****"

# Timeout (seconds) for the TCP reachability check of the SMTP host/port.
CONNECTIVITY_TIMEOUT_SECONDS = 5

SMTP_NOT_CONFIGURED_MESSAGE = (
    "SMTP email is not configured. Set EMAIL_HOST, EMAIL_PORT, and EMAIL_DEFAULT_FROM_EMAIL."
)

# The connectivity check only needs host and port, so it reports a narrower
# requirement than the full delivery path.
SMTP_CONNECTIVITY_NOT_CONFIGURED_MESSAGE = (
    "SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT."
)

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


def environment_overrides(environ=None):
    """Return {model field: env var} for every email field whose env var is set.

    String/number fields count as set only when non-empty; boolean fields use
    presence in the environment so an explicit ``EMAIL_USE_TLS=False`` still
    marks the field as environment-controlled.
    """
    environ = os.environ if environ is None else environ
    overrides = {}
    for field, variable in EMAIL_SETTINGS_FIELDS.items():
        if field in EMAIL_SETTINGS_BOOLEAN_FIELDS:
            is_set = variable in environ
        else:
            is_set = bool(environ.get(variable))
        if is_set:
            overrides[field] = variable
    return overrides


def database_to_environment(configuration):
    """Build an environ-style mapping from a ServerConfiguration row.

    The produced dict reuses ``parse_smtp_configuration`` so every existing
    SMTP validation rule (port range, username+password pairing, TLS/SSL
    mutual exclusion, valid from-address) applies to database settings too.
    """
    port = configuration.email_port
    return {
        "EMAIL_HOST": configuration.email_host or "",
        "EMAIL_PORT": str(port) if port not in (None, "") else "",
        "EMAIL_HOST_USER": configuration.email_host_user or "",
        "EMAIL_HOST_PASSWORD": configuration.email_host_password or "",
        "EMAIL_DEFAULT_FROM_EMAIL": configuration.email_default_from_email or "",
        "EMAIL_USE_TLS": "true" if configuration.email_use_tls else "false",
        "EMAIL_USE_SSL": "true" if configuration.email_use_ssl else "false",
    }


def _first_server_configuration():
    from .models import ServerConfiguration

    try:
        return ServerConfiguration.objects.first()
    except (DatabaseError, DatabaseOperationForbidden):
        # The database may be unavailable (test isolation or startup ordering).
        # A missing row behaves like no email configuration at all.
        return None


def _resolved_environment(configuration=None):
    """Effective SMTP source merged per field.

    The base values come from the ServerConfiguration row (when available) and
    only the EMAIL_* environment variables that are actually present are
    overlaid on top, so a partial environment (e.g. only ``EMAIL_USE_TLS``)
    still fills the remaining fields from the database. Boolean fields use
    presence in the environment, so an explicit ``EMAIL_USE_TLS=False``
    overrides the database value.
    """
    overrides = environment_overrides()
    if configuration is None:
        configuration = _first_server_configuration()
    if not overrides:
        if configuration is None:
            return {}
        return database_to_environment(configuration)
    merged = database_to_environment(configuration) if configuration is not None else {}
    for variable in overrides.values():
        merged[variable] = os.environ.get(variable, "")
    return merged


def _configuration_has_email_fields(configuration):
    """True when any email setting is stored on the ServerConfiguration row."""
    for field in EMAIL_SETTINGS_FIELDS:
        value = getattr(configuration, field, None)
        if field in EMAIL_SETTINGS_BOOLEAN_FIELDS:
            # Stored defaults are False for fresh rows; only an explicit True
            # counts as a configured email setting.
            if value not in (None, False):
                return True
        elif value not in (None, ""):
            return True
    return False


def get_email_status(configuration=None):
    """Return safe capability information without exposing SMTP credentials."""
    if configuration is None:
        configuration = _first_server_configuration()
    if not environment_overrides() and (
        configuration is None or not _configuration_has_email_fields(configuration)
    ):
        return {
            "status": "unavailable",
            "message": SMTP_NOT_CONFIGURED_MESSAGE,
        }
    try:
        parse_smtp_configuration(
            environ=_resolved_environment(configuration=configuration),
            require_complete=True,
        )
    except ImproperlyConfigured as exc:
        return {"status": "invalid", "message": str(exc)}
    return {"status": "configured", "message": "SMTP email is configured."}


def email_settings_payload(configuration):
    """Safe payload for the email configuration endpoint (never the password)."""
    return {
        "email_host": configuration.email_host,
        "email_port": configuration.email_port,
        "email_host_user": configuration.email_host_user,
        "email_password_set": bool(configuration.email_host_password),
        "email_default_from_email": configuration.email_default_from_email,
        "email_use_tls": configuration.email_use_tls,
        "email_use_ssl": configuration.email_use_ssl,
        "environment_overrides": environment_overrides(),
        "effective": get_email_status(configuration=configuration),
    }


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
        return parse_smtp_configuration(environ=_resolved_environment())
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
    # Drive the connection from the resolved (env-or-database) configuration so
    # SMTP settings edited in the UI take effect without a container restart.
    backend = EmailBackend(
        host=smtp.host,
        port=smtp.port,
        username=smtp.username,
        password=smtp.password,
        use_tls=smtp.use_tls,
        use_ssl=smtp.use_ssl,
        fail_silently=False,
    )
    try:
        email = EmailMessage(
            subject=subject, body=body, from_email=smtp.from_email, to=[recipient],
            connection=backend,
        )
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


def check_smtp_connectivity():
    """Open and immediately close a TCP connection to the SMTP host and port.

    Unlike the full delivery path this only needs ``EMAIL_HOST`` and
    ``EMAIL_PORT``; username, password, security mode, and the from-address are
    not required to establish a TCP connection. The check never sends a message.
    """
    environ = _resolved_environment()
    host = str(environ.get("EMAIL_HOST", "")).strip()
    if not host:
        raise EmailConfigurationError(SMTP_CONNECTIVITY_NOT_CONFIGURED_MESSAGE)
    try:
        port = int(str(environ.get("EMAIL_PORT", "")).strip())
    except (TypeError, ValueError) as exc:
        raise EmailConfigurationError(SMTP_CONNECTIVITY_NOT_CONFIGURED_MESSAGE) from exc
    if not 1 <= port <= 65535:
        raise EmailConfigurationError(SMTP_CONNECTIVITY_NOT_CONFIGURED_MESSAGE)
    try:
        with socket.create_connection(
            (host, port), timeout=CONNECTIVITY_TIMEOUT_SECONDS
        ):
            pass
    except socket.gaierror as exc:
        logger.warning(
            "SMTP connectivity check failed: host name could not be resolved",
            extra={"smtp_host": host, "smtp_port": port},
        )
        raise EmailDeliveryError(
            "The SMTP host name could not be resolved. Check EMAIL_HOST."
        ) from exc
    except socket.timeout as exc:
        logger.warning(
            "SMTP connectivity check timed out",
            extra={"smtp_host": host, "smtp_port": port},
        )
        raise EmailDeliveryError(
            "The SMTP server did not respond. Check the host and port, and that "
            "the port is reachable from the container (for Docker, check the "
            "port mapping)."
        ) from exc
    except ConnectionRefusedError as exc:
        logger.warning(
            "SMTP connectivity check was refused",
            extra={"smtp_host": host, "smtp_port": port},
        )
        raise EmailDeliveryError(
            "The connection to the SMTP server was refused. Check the host, "
            "port, and firewall or Docker port mapping."
        ) from exc
    except OSError as exc:
        logger.warning(
            "SMTP connectivity check failed",
            extra={
                "smtp_host": host,
                "smtp_port": port,
                "exception_type": type(exc).__name__,
            },
        )
        raise EmailDeliveryError(EMAIL_DELIVERY_CONNECTION_MESSAGE) from exc
    return {"message": f"SMTP server is reachable at {host}:{port}."}


def email_peer_configuration(peer):
    from .serializers import PeerWithQrSerializer

    recipient = validate_recipient(peer.email_address)
    generated = PeerWithQrSerializer(peer).data
    send_configuration_email(
        f"Tunnel configuration sent from wg-ui-plus for {peer.name}",
        f"The WireGuard configuration for {peer.name} is attached. Keep it safe.",
        recipient, generated["qr"], generated["configuration"],
    )
