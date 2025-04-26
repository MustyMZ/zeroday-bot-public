import asyncio
import aiohttp
import feedparser
import time
import ssl
from datetime import datetime
from telegram import Bot

# Telegram ayarları
TELEGRAM_TOKEN = "7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE"
TELEGRAM_CHAT_ID = "5865934765"

# RSS kaynağı
RSS_FEED_URL = "https://cointelegraph.com/rss"

# SSL uyumsuzlukları için (bazı sunucularda lazım olabiliyor)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

async def analyze_news(title, summary):
    content = (title + " " + summary)[:400]  # İlk 400 karakter
    content_lower = content.lower()

    if any(word in content_lower for word in ["hack", "scam", "rug pull", "exploit", "theft", "loss", "attack", "hacked", "lawsuit", "charges", "arrest"]):
        return "SATIM SİNYALİ (Negatif Haber)"
    elif any(word in content_lower for word in ["partnership", "investment", "adoption", "growth", "bullish", "surge", "rally", "positive", "win", "approval", "support"]):
        return "ALIM SİNYALİ (Pozitif Haber)"
    else:
        return "NÖTR (Belirsiz Haber)"

async def fetch_and_send_news():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RSS_FEED_URL, ssl=ssl_context) as response:
                    data = await response.read()
                    feed = feedparser.parse(data)

                    for entry in feed.entries[:3]:  # İlk 3 haberi alıyoruz
                        title = entry.title
                        summary = entry.summary

                        signal = await analyze_news(title, summary)
                        message = f"ZERODAY Haber Analizi ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')}):\n---\nBaşlık: {title}\nÖzet: {summary[:400]}...\nSonuç: {signal}"

                        if len(message) > 4000:
                            message = message[:3990] + "\n(Sistem tarafından kısaltıldı)"

                        await send_telegram_message(message)
        except Exception as e:
            print(f"Hata oluştu, devam ediliyor: {e}")

        print("1 saat uykuya geçildi...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(fetch_and_send_news())
