import feedparser
import time
import requests
import random
import json

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]
TELEGRAM_BOT_TOKEN = '7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE'
TELEGRAM_CHAT_ID = '6150871845'

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

def classify_news(summary):
    summary_lower = summary.lower()
    if any(word in summary_lower for word in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "SATIM SİNYALİ (Short İşlem Açılabilir)", "short"
    elif any(word in summary_lower for word in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "ALIM SİNYALİ (Alım Fırsatı Görüldü)", "long"
    else:
        return "NÖTR (Bekle ve Gözlemle)", "neutral"

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
                result_text, action = classify_news(summary)
                leverage = f"{random.randint(3, 20)}x"
                yorum = ""

                if action == "long":
                    yorum = f"{matched_coin} için ALIM fırsatı görüldü. Long işlem açılabilir."
                elif action == "short":
                    yorum = f"{matched_coin} için SATIŞ fırsatı görüldü. Short işlem açılabilir."
                else:
                    yorum = f"{matched_coin} için belirgin bir sinyal yok. Beklenmeli."

                json_data = {
                    "action": action,
                    "coins": [matched_coin],
                    "leverage": leverage
                }

                message = f"""ZERODAY Haber Analizi:
---
Başlık: {title}
Özet: {summary}
Sonuç: {result_text}
Yorum: {yorum}
JSON Tahmin: {json.dumps(json_data, ensure_ascii=False)}
Kaynak: {entry.link}
"""
                send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)