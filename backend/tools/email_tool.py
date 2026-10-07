import os
import re
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from langchain.tools import tool


load_dotenv()

EMAIL_TIMEOUT = 10


def _is_valid_email(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


@tool
def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    """
    Send an email to a specified recipient.

    Use this tool only when the user explicitly asks
    to send a research result or report by email.

    This tool performs an external side effect.
    The LangGraph workflow should request user approval
    before executing it.

    Input:
        recipient: Email address of the recipient.
        subject: Email subject.
        body: Email content.

    Output:
        Success or error message.
    """

    if not recipient or not recipient.strip():
        return "Error: Recipient email cannot be empty."

    recipient = recipient.strip()

    if not _is_valid_email(recipient):
        return (
            "Error: Invalid recipient email address."
        )

    if not subject or not subject.strip():
        return "Error: Email subject cannot be empty."

    if not body or not body.strip():
        return "Error: Email body cannot be empty."

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM")

    if not smtp_host:
        return "Error: SMTP_HOST is missing from .env"

    if not smtp_port:
        return "Error: SMTP_PORT is missing from .env"

    if not smtp_username:
        return "Error: SMTP_USERNAME is missing from .env"

    if not smtp_password:
        return "Error: SMTP_PASSWORD is missing from .env"

    if not email_from:
        return "Error: EMAIL_FROM is missing from .env"

    try:
        message = EmailMessage()

        message["From"] = email_from
        message["To"] = recipient
        message["Subject"] = subject.strip()

        message.set_content(
            body.strip()
        )

        with smtplib.SMTP(
            smtp_host,
            int(smtp_port),
            timeout=EMAIL_TIMEOUT,
        ) as server:

            server.starttls()

            server.login(
                smtp_username,
                smtp_password,
            )

            server.send_message(
                message
            )

        return "Email sent successfully."

    except Exception as error:
        return (
            f"Error: Email sending failed: "
            f"{str(error)}"
        )