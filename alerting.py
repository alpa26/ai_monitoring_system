import requests
import smtplib

TG_TOKEN = "YOUR_TOKEN"
TG_CHAT_ID = "YOUR_CHAT_ID"

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