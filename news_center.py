import os
from dotenv import load_dotenv
import feedparser
import requests
import time
import random
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]
TELEGRAM_BOT_TOKEN = '7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE'
TELEGRAM_CHAT_ID = '6150871845'

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

def translate_to_turkish(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Metni Türkçeye çevir."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Çeviri hatası: {e}"

def classify_news(text):
    lower = text.lower()
    if any(x in lower for x in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "SATIM SİNYALİ (Short İşlem Açılabilir)", "short", random.choice(["5x", "7x", "10x", "12x", "20x"])
    elif any(x in lower for x in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "ALIM SİNYALİ (Alım Fırsatı Görüldü)", "long", random.choice(["5x", "7x", "10x", "12x", "20x"])
    else:
        return "NÖTR (Bekle ve Gözlemle)", "neutral", random.choice(["3x", "5x", "10x", "20x"])

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print("Telegram gönderim hatası:", response.text)
    except Exception as e:
        print("Telegram bağlantı hatası:", str(e))

def process_feed():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            title = entry.title
            summary = entry.summary[:400]
            full_text = f"{title}\n{summary}"

            matched_coin = next((coin for coin in ALTCOINS if coin.lower() in full_text.lower()), None)
            if matched_coin:
                translated_title = translate_to_turkish(title)
                translated_summary = translate_to_turkish(summary)

                signal, action, leverage = classify_news(summary)
                yorum = f"{matched_coin} için {'SATIŞ' if action == 'short' else 'ALIM' if action == 'long' else 'belirgin bir sinyal yok'}. "
                if action == "short":
                    yorum += "Short işlem açılabilir."
                elif action == "long":
                    yorum += "Long işlem açılabilir."
                else:
                    yorum += "Beklenmeli."

                json_strateji = f"""{{
"action": "{action}",
"coins": ["{matched_coin}"],
"leverage": "{leverage}"
}}"""

                message = f"""ZERODAY Haber Analizi:
---
Başlık: {translated_title}
Özet: {translated_summary}
Sonuç: {signal}
Yorum: {yorum}
Kaynak: {entry.link}
JSON Strateji:
{json_strateji}
"""
                send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler kontrol ediliyor...")
        process_feed()
        print("1 saat uykuya geçiliyor...")
        time.sleep(3600)