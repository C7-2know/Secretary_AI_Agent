import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER = os.getenv("SENDGRID_SENDER", "no-reply@example.com")

def send_email(to_email: str, subject: str, html: str):
    if not SENDGRID_API_KEY:
        print(f"[DRY-RUN EMAIL] To: {to_email}\nSubject: {subject}\n{html}")
        return {"status": "dry-run"}
    message = Mail(
        from_email=SENDER,
        to_emails=to_email,
        subject=subject,
        html_content=html
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    resp = sg.send(message)
    return {"status": resp.status_code}
