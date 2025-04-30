import os
import time
import openai
import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = "7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE"
TELEGRAM_CHAT_ID = "@ZERODAYANALIZ"

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

def translate_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate to Turkish:"},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("Çeviri hatası:", str(e))
        return text

def classify_news(summary):
    lower = summary.lower()
    if any(word in lower for word in ["hack", "lawsuit", "fine", "ban", "investigation", "crash"]):
        return "SATIM SİNYALİ", "short", f"{get_random_leverage()}x"
    elif any(word in lower for word in ["partnership", "adoption", "bullish", "investment", "rally"]):
        return "ALIM SİNYALİ", "long", f"{get_random_leverage()}x"
    else:
        return "NÖTR", "neutral", "3x"

def get_random_leverage():
    from random import choice
    return choice([3, 5, 7, 10, 15, 20])

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data, timeout=10)
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
            full_text = f"{title} {summary}"

            matched_coin = None
            for coin in ALTCOINS:
                if coin.lower() in full_text.lower():
                    matched_coin = coin
                    break

            if matched_coin:
                translated_title = translate_text(title)
                translated_summary = translate_text(summary)
                result, action, leverage = classify_news(summary)

                yorum = ""
                if action == "long":
                    yorum = f"{matched_coin} için ALIM fırsatı görüldü. Long işlem açılabilir."
                elif action == "short":
                    yorum = f"{matched_coin} için SATIŞ fırsatı görüldü. Short işlem açılabilir."
                else:
                    yorum = f"{matched_coin} için belirgin bir sinyal yok. Beklenmeli."

                message = f"""ZERODAY Haber Analizi:
---
Başlık: {translated_title}
Özet: {translated_summary}
Sonuç: {result}
Yorum: {yorum}
Kaynak: {entry.link}

JSON Sinyali:
{{
  "action": "{action}",
  "coins": ["{matched_coin}"],
  "leverage": "{leverage}"
}}
"""
                send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)