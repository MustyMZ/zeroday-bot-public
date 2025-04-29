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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

def translate_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bu metni Türkçeye çevir."},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("Çeviri hatası:", str(e))
        return text

def classify_news(summary):
    summary_lower = summary.lower()
    if any(word in summary_lower for word in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "SATIM SİNYALİ (Short İşlem Açılabilir)"
    elif any(word in summary_lower for word in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "ALIM SİNYALİ (Alım Fırsatı Görüldü)"
    else:
        return "NÖTR (Bekle ve Gözlemle)"

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
            title_raw = entry.title
            summary_raw = entry.summary[:400]

            title = translate_text(title_raw)
            summary = translate_text(summary_raw)

            full_text = f"{title} {summary}"

            matched_coin = None
            for coin in ALTCOINS:
                if coin.lower() in full_text.lower():
                    matched_coin = coin
                    break

            if matched_coin:
                result = classify_news(summary)
                yorum = ""
                action = "neutral"
                leverage = f"{random.randint(3, 20)}x"
                if "ALIM" in result:
                    yorum = f"{matched_coin} için ALIM fırsatı görüldü. Long işlem açılabilir."
                    action = "long"
                elif "SATIM" in result:
                    yorum = f"{matched_coin} için SATIŞ fırsatı görüldü. Short işlem açılabilir."
                    action = "short"
                else:
                    yorum = f"{matched_coin} için belirgin bir sinyal yok. Beklenmeli."

                json_strateji = f'''{{
"action": "{action}",
"coins": ["{matched_coin}"],
"leverage": "{leverage}"
}}'''

                message = f"""ZERODAY Haber Analizi:
---
Başlık: {title}
Özet: {summary}
Sonuç: {result}
Yorum: {yorum}
Kaynak: {entry.link}
JSON Strateji:
{json_strateji}
"""
                send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)