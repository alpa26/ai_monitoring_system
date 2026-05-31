import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import random

TG_TOKEN = "TOKEN"
TG_CHAT_ID = "CHAT_ID"

VK_TOKEN = ""
USER_ID = ""

EMAIL = "r2207368@gmail.com"
APP_PASSWORD = "APP_PASSWORD"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TG_CHAT_ID,
        "text": message
    })

def send_email(message):
    try:
        msg = MIMEMultipart()

        msg["From"] = EMAIL
        msg["To"] = EMAIL
        msg["Subject"] = "AI Monitoring Alert"

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login(EMAIL, APP_PASSWORD)

        server.send_message(msg)

        server.quit()

        print("EMAIL ALERT SENT")

    except Exception as e:
        print("EMAIL ERROR:", e)


def send_vk_alert(message):
    r = requests.get(
        "https://api.vk.com/method/users.get",
        params={
            "user_ids": USER_ID,
            "access_token": VK_TOKEN,
            "v": "5.131"
        }
    )

    data = r.json()

    user_id = data["response"][0]["id"]

    res = requests.post(
        "https://api.vk.com/method/messages.send",
        data={
            "user_id": user_id,
            "message": message,
            "random_id": random.randint(1, 999999),
            "access_token": VK_TOKEN,
            "v": "5.131"
        }
    )