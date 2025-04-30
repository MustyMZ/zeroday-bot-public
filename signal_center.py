import os
import time
import feedparser
import requests
from dotenv import load_dotenv
import openai
import random

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]

def translate_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Metni Türkçeye çevir, sadece çeviriyi döndür."
            }, {
                "role": "user",
                "content": text
            }]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Çeviri hatası: {e}"

def classify_news(text):
    text = text.lower()
    if any(w in text for w in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "short"
    elif any(w in text for w in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "long"
    else:
        return "neutral"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def process_feeds():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:
            title_en = entry.title
            summary_en = entry.summary[:400]

            title_tr = translate_text(title_en)
            summary_tr = translate_text(summary_en)

            full_text = f"{title_en} {summary_en}"
            affected = [coin for coin in ALTCOINS if coin.lower() in full_text.lower()]
            affected = affected if affected else random.sample(ALTCOINS, 3)

            action = classify_news(full_text)
            leverage = f"{random.randint(3, 20)}x"

            yorum = ""
            if action == "long":
                yorum = f"{', '.join(affected)} için ALIM fırsatı görüldü. Long işlem açılabilir."
            elif action == "short":
                yorum = f"{', '.join(affected)} için SATIŞ baskısı var. Short işlem düşünülebilir."
            else:
                yorum = f"{', '.join(affected)} için belirgin sinyal yok. Beklenmeli."

            json_data = {
                "action": action,
                "coins": affected[:5],
                "leverage": leverage
            }

            message = f"""ZERODAY Haber Analizi:
---
Başlık: {title_tr}
Özet: {summary_tr}
Yorum: {yorum}

JSON Öneri:
{json_data}

Kaynak: {entry.link}
"""
            send_telegram(message)

if __name__ == "__main__":
    while True:
        print("Haberler taranıyor...")
        process_feeds()
        print("1 saat uyku...")
        time.sleep(3600)