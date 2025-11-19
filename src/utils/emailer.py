import smtplib
from email.mime.text import MIMEText
from typing import List
from src.core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM


def send_email(subject: str, body: str, recipients: List[str]) -> None:
    """
    Надсилає електронного листа через SMTP-сервер, використовуючи TLS.
    """
    if not SMTP_HOST or not recipients:
        return
        
    # Створюємо повідомлення
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(recipients)

    try:
        # Встановлюємо з'єднання та надсилаємо лист
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Захист з'єднання
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipients, msg.as_string())
    except Exception as e:
        # У реальному проекті тут має бути логування помилок
        print(f"Error sending email: {e}")