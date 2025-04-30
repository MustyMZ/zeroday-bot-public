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
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.altcoinbuzz.io/feed/"
]

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            print("Telegram gönderim hatası:", response.text)
    except Exception as e:
        print("Telegram bağlantı hatası:", str(e))

def ask_gpt_analysis(title, summary):
    try:
        prompt = (
            "You are a crypto trading signal assistant. Analyze this crypto news and give:
"
            f"- Most affected 3 to 5 coins (from this list: {ALTCOINS}).
"
            "- Action (long, short, or neutral).
"
            "- Leverage between 3x and 20x.

"
            f"News Title: {title}
"
            f"Summary: {summary}

"
            "Return JSON like:
"
            '{
'
            '  "action": "long",
'
            '  "coins": ["SOL", "OP"],
'
            '  "leverage": "10x"
'
            '}'
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful crypto analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )

        result = response.choices[0].message.content
        return result.strip()
    except Exception as e:
        return f"GPT Analiz Hatası: {str(e)}"

def process_feed():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:
            title = entry.title
            summary = entry.summary[:400]
            link = entry.link

            gpt_result = ask_gpt_analysis(title, summary)

            message = f"""ZERODAY GPT Haber Analizi:
Başlık: {title}
Özet: {summary}
GPT Yorumu:
{gpt_result}
Kaynak: {link}
"""
            send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler analiz ediliyor...")
        process_feed()
        print("1 saat uykuya geçiliyor...")
        time.sleep(3600)
