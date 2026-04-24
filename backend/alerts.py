"""
ThirdEye — Alert System
Multi-channel notifications: Email (Gmail SMTP), SMS (Twilio), WebSocket push.
Gracefully skips channels when credentials are missing.
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("thirdeye.alerts")


class AlertSystem:
    """Send alerts across multiple channels when matches are found."""

    def __init__(self, db):
        self.db = db
        self._gmail_user = os.getenv("GMAIL_USER", "")
        self._gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "")
        self._alert_email = os.getenv("ALERT_EMAIL", "")
        self._twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self._twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self._twilio_from = os.getenv("TWILIO_FROM_NUMBER", "")
        self._alert_phone = os.getenv("ALERT_PHONE_NUMBER", "")

    async def send_alert(self, person_id: str, match_data: dict):
        """Send alert across all configured channels."""
        channels_sent = []

        # Email
        if self._gmail_user and self._gmail_pass and self._alert_email:
            success = await self._send_email(person_id, match_data)
            if success:
                channels_sent.append("email")

        # SMS
        if self._twilio_sid and self._twilio_token and self._alert_phone:
            success = await self._send_sms(person_id, match_data)
            if success:
                channels_sent.append("sms")

        # Log the alerts
        for channel in channels_sent:
            await self.db.log_alert(
                person_id=person_id,
                match_id=match_data.get("match_id"),
                channel=channel,
                recipient=self._alert_email if channel == "email" else self._alert_phone,
                payload=match_data,
                status="sent",
            )

        if not channels_sent:
            logger.info("No alert channels configured — match logged only")

        return channels_sent

    async def _send_email(self, person_id: str, match_data: dict) -> bool:
        """Send email alert via Gmail SMTP."""
        try:
            confidence = match_data.get("confidence", 0)
            label = match_data.get("label", "MATCH")
            source = match_data.get("source", "Unknown")
            location = match_data.get("location", "Unknown location")

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 ThirdEye Alert: {label} ({confidence:.0%}) — {source}"
            msg["From"] = self._gmail_user
            msg["To"] = self._alert_email

            html = f"""
            <html><body style="font-family:Arial,sans-serif;background:#1a1a2e;color:#e0e0e0;padding:20px;">
            <div style="max-width:600px;margin:0 auto;background:#16213e;border-radius:12px;padding:24px;border:1px solid #0f3460;">
                <h1 style="color:#00d4ff;margin-top:0;">👁️ ThirdEye Alert</h1>
                <div style="background:#0f3460;border-radius:8px;padding:16px;margin:16px 0;">
                    <h2 style="color:#e94560;margin-top:0;">{label}</h2>
                    <p><strong>Confidence:</strong> {confidence:.1%}</p>
                    <p><strong>Source:</strong> {source}</p>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Time:</strong> {match_data.get('timestamp', 'N/A')}</p>
                </div>
                {f'<p><a href="{match_data.get("post_url","")}" style="color:#00d4ff;">View Source →</a></p>' if match_data.get("post_url") else ''}
                <hr style="border-color:#0f3460;">
                <p style="color:#666;font-size:12px;">ThirdEye Missing Person Intelligence System</p>
            </div>
            </body></html>
            """

            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self._gmail_user, self._gmail_pass)
                server.send_message(msg)

            logger.info(f"Email alert sent to {self._alert_email}")
            return True

        except Exception as e:
            logger.error(f"Email alert failed: {e}")
            await self.db.log_alert(
                person_id=person_id, channel="email",
                status="failed", error_message=str(e),
            )
            return False

    async def _send_sms(self, person_id: str, match_data: dict) -> bool:
        """Send SMS alert via Twilio."""
        try:
            from twilio.rest import Client

            client = Client(self._twilio_sid, self._twilio_token)
            confidence = match_data.get("confidence", 0)
            label = match_data.get("label", "MATCH")
            source = match_data.get("source", "Unknown")

            body = (
                f"👁️ ThirdEye Alert\n"
                f"{label} ({confidence:.0%})\n"
                f"Source: {source}\n"
                f"Location: {match_data.get('location', 'Unknown')}\n"
                f"View: {match_data.get('post_url', 'N/A')}"
            )

            message = client.messages.create(
                body=body, from_=self._twilio_from, to=self._alert_phone
            )

            logger.info(f"SMS alert sent: {message.sid}")
            return True

        except Exception as e:
            logger.error(f"SMS alert failed: {e}")
            await self.db.log_alert(
                person_id=person_id, channel="sms",
                status="failed", error_message=str(e),
            )
            return False
