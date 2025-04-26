import asyncio
import feedparser
from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID

# Telegram bot başlat
bot = Bot(token=TELEGRAM_TOKEN)

# Daha önce işlenen haberlerin ID'lerini tutacağız
processed_entries = set()

async def send_telegram_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def analyze_sentiment(text):
    text = text.lower()
    positive_words = ['pump', 'bullish', 'record high', 'new high', 'positive', 'adoption', 'growth', 'support', 'rally', 'rebound', 'booming', 'recovery']
    negative_words = ['dump', 'bearish', 'collapse', 'lawsuit', 'negative', 'ban', 'restrict', 'fine', 'decline', 'fall', 'hacker', 'hack', 'crash']

    pos = any(word in text for word in positive_words)
    neg = any(word in text for word in negative_words)

    if pos and not neg:
        return "ALIM SİNYALİ (Pozitif Haber)"
    elif neg and not pos:
        return "SATIM SİNYALİ (Negatif Haber)"
    else:
        return "NÖTR"

async def fetch_and_analyze_news():
    url = "https://cointelegraph.com/rss"  # RSS kaynağı
    feed = feedparser.parse(url)

    for entry in feed.entries:
        if entry.id not in processed_entries:
            title = entry.title
            summary = entry.summary
            link = entry.link

            # Tüm haberi özet olarak kısaltıyoruz (400 karakter)
            short_summary = summary.strip().replace('\n', ' ')[:400]

            # Sentiment analizi tüm haber özeti üzerinden yapılıyor
            signal = analyze_sentiment(summary)

            # Mesaj formatı
            message = (
                f"ZERODAY Haber Analizi:\n\n"
                f"Başlık: {title}\n\n"
                f"Özet: {short_summary}\n\n"
                f"Sonuç: {signal}"
            )

            await send_telegram_message(message)

            print(f"Haber işlendi: {title}")
            processed_entries.add(entry.id)

async def main():
    while True:
        await fetch_and_analyze_news()
        await asyncio.sleep(600)  # 10 dakikada bir kontrol et

if __name__ == "__main__":
    asyncio.run(main())
