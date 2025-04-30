import feedparser
import time
import requests
import random

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]

TELEGRAM_BOT_TOKEN = '7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE'
TELEGRAM_CHAT_ID = '6150871845'

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptopotato.com/feed/",
    "https://u.today/rss"
]

def classify_news(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ["hack", "lawsuit", "ban", "exploit", "scam", "regulation"]):
        return "short"
    elif any(word in text_lower for word in ["adoption", "partnership", "launch", "bullish", "invest", "integration"]):
        return "long"
    else:
        return "neutral"

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
            summary = entry.summary
            full_text = f"{title} {summary}"

            matched = [coin for coin in ALTCOINS if coin.lower() in full_text.lower()]
            if matched:
                action = classify_news(full_text)
                leverage = f"{random.randint(3, 20)}x"
                coins = random.sample(matched, min(3, len(matched)))

                yorum = {
                    "long": "Olumlu haber. Long işlem açılabilir.",
                    "short": "Olumsuz haber. Short işlem açılabilir.",
                    "neutral": "Belirsiz haber. İşlem önerilmez."
                }[action]

                json_sinyal = {
                    "action": action,
                    "coins": coins,
                    "leverage": leverage
                }

                mesaj = f"""ZERODAY Haber Analizi:
---
Başlık: {title}
Özet: {summary[:300]}...
Sinyal: {yorum}

JSON format:
{json_sinyal}
Kaynak: {entry.link}
"""
                send_to_telegram(mesaj)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)