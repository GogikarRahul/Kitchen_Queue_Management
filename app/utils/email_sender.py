# app/utils/email_sender.py

from fastapi_mail import FastMail, MessageSchema
from app.core.email_config import conf


async def send_email(subject: str, recipients: list[str], body: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)
