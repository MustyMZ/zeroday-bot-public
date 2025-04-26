import feedparser
import asyncio
import re
from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID

bot = Bot(token=TELEGRAM_TOKEN)

POSITIVE_KEYWORDS = ["ETF", "approval", "partnership", "integration", "bull", "uptrend", "surge", "growth"]
NEGATIVE_KEYWORDS = ["hack", "lawsuit", "ban", "sell-off", "downtrend", "collapse", "scam"]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

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

async def main():
    feed = feedparser.parse("https://cointelegraph.com/rss")
    latest_entry = feed.entries[0]
    title = latest_entry.title
    summary_raw = latest_entry.summary
    summary = clean_html(summary_raw)
    link = latest_entry.link
    sentiment = analyze_sentiment(title, summary)

    message = f"""ZERODAY Haber Analizi ({feed.entries[0].published}):
---
Başlık: {title}
Özet: {summary}

Kaynak: {link}

Sonuç: {sentiment}"""
    
    print(message)
    await send_to_telegram(message)

if __name__ == "__main__":
    asyncio.run(main())
