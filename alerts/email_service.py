import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()

SENDER = os.getenv("EMAIL_SENDER")
PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER = os.getenv("EMAIL_RECEIVER")


def send_anomaly_alert(
    city: str,
    pm25: float,
    anomaly_score: float,
    recorded_at: datetime,
) -> bool:
    """
    Send an email alert when an anomaly is detected.
    Returns True if sent successfully, False otherwise.
    """

    if not all([SENDER, PASSWORD, RECEIVER]):
        print(
            "Email not configured. "
            "Add EMAIL_SENDER, EMAIL_PASSWORD, "
            "EMAIL_RECEIVER to .env"
        )
        return False

    # ── Build the email ──────────────────────────────────

    subject = (
        f"⚠️ SmartCampus AI — PM2.5 Anomaly Detected "
        f"in {city}"
    )

    # Plain text version (fallback for simple email clients)
    plain_text = f"""
SmartCampus AI — Anomaly Alert

An abnormal PM2.5 reading was detected.

Location     : {city}
PM2.5 Value  : {pm25} µg/m³
Anomaly Score: {anomaly_score:.4f}
Recorded At  : {recorded_at}
Alert Sent At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This reading has been flagged as potentially dangerous.
Please check the SmartCampus AI dashboard for details.

-- SmartCampus AI Monitoring System
    """.strip()

    # HTML version (rich email with colors)
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;
                 max-width: 600px;
                 margin: 0 auto;
                 padding: 20px;">

        <div style="background: #ff4444;
                    color: white;
                    padding: 16px 20px;
                    border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">
                ⚠️ PM2.5 Anomaly Detected
            </h2>
        </div>

        <div style="border: 1px solid #ddd;
                    border-top: none;
                    padding: 20px;
                    border-radius: 0 0 8px 8px;">

            <p style="color: #555; margin-top: 0;">
                SmartCampus AI has detected an abnormal
                PM2.5 reading that requires attention.
            </p>

            <table style="width: 100%;
                          border-collapse: collapse;">
                <tr style="background: #f9f9f9;">
                    <td style="padding: 10px;
                               font-weight: bold;
                               border-bottom: 1px solid #eee;
                               width: 40%;">
                        Location
                    </td>
                    <td style="padding: 10px;
                               border-bottom: 1px solid #eee;">
                        {city}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;
                               font-weight: bold;
                               border-bottom: 1px solid #eee;">
                        PM2.5 Value
                    </td>
                    <td style="padding: 10px;
                               border-bottom: 1px solid #eee;
                               color: #ff4444;
                               font-weight: bold;">
                        {pm25} µg/m³
                    </td>
                </tr>
                <tr style="background: #f9f9f9;">
                    <td style="padding: 10px;
                               font-weight: bold;
                               border-bottom: 1px solid #eee;">
                        Anomaly Score
                    </td>
                    <td style="padding: 10px;
                               border-bottom: 1px solid #eee;">
                        {anomaly_score:.4f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;
                               font-weight: bold;
                               border-bottom: 1px solid #eee;">
                        Recorded At
                    </td>
                    <td style="padding: 10px;
                               border-bottom: 1px solid #eee;">
                        {recorded_at}
                    </td>
                </tr>
                <tr style="background: #f9f9f9;">
                    <td style="padding: 10px;
                               font-weight: bold;">
                        Alert Sent At
                    </td>
                    <td style="padding: 10px;">
                        {datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S'
                        )}
                    </td>
                </tr>
            </table>

            <div style="margin-top: 20px;
                        padding: 12px;
                        background: #fff3cd;
                        border-radius: 6px;
                        border-left: 4px solid #ffc107;">
                <strong>Recommended action:</strong>
                Check the SmartCampus AI dashboard
                and consider issuing a health advisory
                if readings remain elevated.
            </div>

            <p style="color: #999;
                      font-size: 12px;
                      margin-top: 20px;">
                This alert was generated automatically
                by SmartCampus AI Monitoring System.
            </p>
        </div>
    </body>
    </html>
    """

    # ── Build MIME message ───────────────────────────────
    # MIME = format that lets emails contain both
    # plain text and HTML in one message

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER
    message["To"] = RECEIVER

    # Attach both versions — email client picks the best one
    message.attach(MIMEText(plain_text, "plain"))
    message.attach(MIMEText(html_body, "html"))

    # ── Send via Gmail SMTP ──────────────────────────────
    try:
        # Port 587 = TLS encrypted SMTP (secure)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:

            # Start TLS encryption
            server.starttls()

            # Login with app password
            server.login(SENDER, PASSWORD)

            # Send the email
            server.sendmail(
                SENDER,
                RECEIVER,
                message.as_string(),
            )

        print(
            f"Alert email sent to {RECEIVER} "
            f"for anomaly in {city}"
        )
        return True

    except smtplib.SMTPAuthenticationError:
        print(
            "Gmail authentication failed. "
            "Check your app password in .env"
        )
        return False

    except smtplib.SMTPException as error:
        print(f"Email send failed: {error}")
        return False


if __name__ == "__main__":
    # Quick test — sends a real test email
    print("Sending test alert email...")

    success = send_anomaly_alert(
        city="Delhi — Test",
        pm25=185.5,
        anomaly_score=-0.1832,
        recorded_at=datetime.now(),
    )

    if success:
        print("Test email sent! Check your inbox.")
    else:
        print("Test email failed. Check .env settings.")