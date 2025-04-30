import os
import feedparser
import time
import requests
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
                {"role": "system", "content": "You are a translator from English to Turkish."},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"(Çeviri Hatası: {str(e)})"

def classify_news(summary):
    lower = summary.lower()
    if any(word in lower for word in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "SATIM SİNYALİ", "short", "12x"
    elif any(word in lower for word in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "ALIM SİNYALİ", "long", "10x"
    else:
        return "NÖTR", "neutral", "3x"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
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
            title_en = entry.title
            summary_en = entry.summary[:400]
            full_text = f"{title_en} {summary_en}"

            matched_coin = None
            for coin in ALTCOINS:
                if coin.lower() in full_text.lower():
                    matched_coin = coin
                    break

            if matched_coin:
                result, action, leverage = classify_news(summary_en)

                try:
                    title_tr = translate_text(title_en)
                    summary_tr = translate_text(summary_en)
                except:
                    title_tr = title_en
                    summary_tr = summary_en

                yorum = ""
                if action == "long":
                    yorum = f"{matched_coin} için ALIM fırsatı görüldü. Long işlem açılabilir."
                elif action == "short":
                    yorum = f"{matched_coin} için SATIŞ fırsatı görüldü. Short işlem açılabilir."
                else:
                    yorum = f"{matched_coin} için belirgin bir sinyal yok. Beklenmeli."

                mesaj = f"""ZERODAY Haber Analizi:
---
Başlık: {title_tr}
Özet: {summary_tr}
Sonuç: {result}
Yorum: {yorum}
Kaynak: {entry.link}

JSON Format:
{{
  "action": "{action}",
  "coins": ["{matched_coin}"],
  "leverage": "{leverage}"
}}"""

                send_to_telegram(mesaj)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)