import feedparser
import os
import openai
import time
import requests
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APT", "SHIB", "PEPE", "FLOKI", "INJ", "LDO", "RUNE"]

RSS_FEEDS = [
    "https://cryptonews.com/news/feed",
    "https://u.today/rss",
    "https://cryptopotato.com/feed",
    "https://coinpedia.org/feed/"
]

def gpt_analyze_news(title, summary):
    try:
        prompt = f"""Başlık: {title}\n\nÖzet: {summary}\n\nBu haberin yatırımcıya etkisini değerlendir. LONG / SHORT / NEUTRAL olarak sınıflandır. Ayrıca JSON formatında 'action', 'coins' ve 'leverage' verilerini üret (örnek: {{'action': 'long', 'coins': ['OP'], 'leverage': '10x'}})."""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sen bir kripto para analiz uzmanısın. Verilen haber başlığı ve özetine göre yatırımcıya yön gösteren karar ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"GPT analiz hatası: {e}"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def main():
    sent_links = set()
    while True:
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                link = entry.link
                if link in sent_links:
                    continue
                sent_links.add(link)

                title = entry.title
                summary = entry.summary if hasattr(entry, "summary") else ""
                analysis = gpt_analyze_news(title, summary)

                message = f"<b>ZERODAY GPT Analizi:</b>\n\n<b>Başlık:</b> {title}\n<b>Özet:</b> {summary}\n<b>Sonuç:</b> {analysis}\n\n<b>Kaynak:</b> {link}"
                send_to_telegram(message)
                # time.sleep(3)  # Her haber sonrası 3 saniye bekleme

        time.sleep(3600)  # 1 saatte bir tüm RSS kaynaklarını tekrar tarar

if __name__ == "__main__":
    main()