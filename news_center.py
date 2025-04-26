import feedparser
import asyncio
from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID

bot = Bot(token=TELEGRAM_TOKEN)

POSITIVE_KEYWORDS = ["ETF", "approval", "partnership", "investment", "bullish", "record", "profit", "launch"]
NEGATIVE_KEYWORDS = ["hack", "lawsuit", "ban", "sell-off", "bearish", "loss", "fraud", "collapse"]

async def send_to_telegram(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def analyze_sentiment(title, summary):
    combined_text = f"{title} {summary}".lower()
    positive_score = sum(word.lower() in combined_text for word in POSITIVE_KEYWORDS)
    negative_score = sum(word.lower() in combined_text for word in NEGATIVE_KEYWORDS)

    if positive_score > negative_score:
        return "ALIM SİNYALİ (Pozitif Haber)"
    elif negative_score > positive_score:
        return "SATIM SİNYALİ (Negatif Haber)"
    else:
        return "NÖTR (Belirsiz Haber)"

async def fetch_and_analyze_news():
    feed_url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print("RSS feed boş geldi.")
        return

    latest_entry = feed.entries[0]  # Son çıkan haber
    title = latest_entry.title
    summary = latest_entry.summary if hasattr(latest_entry, "summary") else ""
    link = latest_entry.link

    sentiment = analyze_sentiment(title, summary)

    from datetime import datetime
    message_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    message = f"""ZERODAY Haber Analizi ({message_time}):
---
Başlık: {title}
Özet: {summary[:300]}...
Kaynak: {link}

Sonuç: {sentiment}
"""

    print(message)
    await send_to_telegram(message)

async def loop_news_checker():
    while True:
        await fetch_and_analyze_news()
        print("10 dakika uyku...")
        await asyncio.sleep(600)  # 600 saniye = 10 dakika

if __name__ == "__main__":
    asyncio.run(loop_news_checker())
