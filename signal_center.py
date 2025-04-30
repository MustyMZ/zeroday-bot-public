import feedparser
import time
import requests
import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
                {"role": "system", "content": "Metinleri Türkçeye çeviren bir asistansın."},
                {"role": "user", "content": f"Lütfen aşağıdaki metni Türkçeye çevir: {text}"}
            ],
            temperature=0.3
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("Çeviri hatası:", e)
        return text

def classify_news(summary):
    summary_lower = summary.lower()
    if any(word in summary_lower for word in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "SATIM SİNYALİ (Short İşlem Açılabilir)", "short"
    elif any(word in summary_lower for word in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "ALIM SİNYALİ (Alım Fırsatı Görüldü)", "long"
    else:
        return "NÖTR (Bekle ve Gözlemle)", "neutral"

def generate_json_signal(action_type, coin):
    import random
    leverage = f"{random.randint(3, 20)}x"
    coins = [coin]
    return {
        "action": action_type,
        "coins": coins,
        "leverage": leverage
    }

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
        for entry in feed.entries[:5]:
            title_en = entry.title
            summary_en = entry.summary[:500]

            translated_title = translate_text(title_en)
            translated_summary = translate_text(summary_en)
            full_text = f"{translated_title} {translated_summary}"

            matched_coin = None
            for coin in ALTCOINS:
                if coin.lower() in full_text.lower():
                    matched_coin = coin
                    break

            if matched_coin:
                classification, action = classify_news(summary_en)
                yorum = f"{matched_coin} için {classification}"
                json_signal = generate_json_signal(action, matched_coin)

                message = f"""ZERODAY Haber Analizi:
---
Başlık: {translated_title}
Özet: {translated_summary}
Sonuç: {classification}
Yorum: {yorum}
JSON Sinyal: {json_signal}
Kaynak: {entry.link}
"""
                send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)