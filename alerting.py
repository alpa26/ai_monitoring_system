import requests
import smtplib
import random

TG_TOKEN = "YOUR_TOKEN"
TG_CHAT_ID = "YOUR_CHAT_ID"

VK_TOKEN = ""
USER_ID = ""

smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
smtpObj.starttls()
smtpObj.login('justkiddingboat@gmail.com', 'just123kidding')

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TG_CHAT_ID,
        "text": message
    })

def send_email(message):
    smtpObj.sendmail("justkiddingboat@gmail.com", "michael.byrne@vice.com", message)
    smtpObj.quit()


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