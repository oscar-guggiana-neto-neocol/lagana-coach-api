from email.message import EmailMessage
import logging
import smtplib
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, **context) -> str:
    template = env.get_template(template_name)
    return template.render(**context)


def send_email(subject: str, to_email: str, html_body: str) -> None:
    if not settings.smtp_host:
        logger.warning("SMTP not configured. Skipping email send to %s", to_email)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to_email
    message.set_content("This email requires an HTML capable client.")
    message.add_alternative(html_body, subtype="html")

    try:
        if settings.smtp_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 587) as smtp:
                smtp.starttls()
                if settings.smtp_user and settings.smtp_password:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 25) as smtp:
                if settings.smtp_user and settings.smtp_password:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - logged for observability
        logger.error("Failed to send email: %s", exc)


def send_password_reset_email(to_email: str, reset_link: str, full_name: Optional[str]) -> None:
    html_body = render_template(
        "email/password_reset.html",
        reset_link=reset_link,
        full_name=full_name,
    )
    send_email(subject="Reset your LaganaCoach password", to_email=to_email, html_body=html_body)
