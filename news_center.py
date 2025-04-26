import feedparser
import asyncio
from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID

bot = Bot(token=TELEGRAM_TOKEN)

POSITIVE_KEYWORDS = ["ETF", "approval", "partnership", "integration", "bull", "rally", "growth", "gain"]
NEGATIVE_KEYWORDS = ["hack", "lawsuit", "ban", "sell-off", "bear", "down", "loss"]

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
    feed_url = "https://cointelegraph.com/rss"
    while True:
        feed = feedparser.parse(feed_url)

        if feed.entries:
            latest_entry = feed.entries[0]
            title = latest_entry.title
            summary = latest_entry.summary

            # Burada özet uzunluğunu 500 karakter ile sınırlandırıyoruz
            summary = summary[:500] + "..." if len(summary) > 500 else summary

            sentiment = analyze_sentiment(title, summary)
            link = latest_entry.link

            message = (
                f"ZERODAY Haber Analizi ({feed.entries[0].published}):\n"
                f"---\n"
                f"Başlık: {title}\n"
                f"Özet: {summary}\n"
                f"Kaynak: {link}\n"
                f"\nSonuç: {sentiment}"
            )

            print(message)
            await send_to_telegram(message)

        await asyncio.sleep(3600)  # 1 saat bekle

if __name__ == "__main__":
    asyncio.run(main())
