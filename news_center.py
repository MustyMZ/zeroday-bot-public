import feedparser
import asyncio
import aiohttp
import datetime

# Telegram bilgileri
TELEGRAM_TOKEN = '7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE'
TELEGRAM_CHAT_ID = '6450857197'

# Tarama yapılacak coinler
COINLER = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'DOGE']

# Haber kaynakları
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/",
    "https://u.today/rss",
    "https://decrypt.co/feed"
]

# Hangi kelimeler olumlu
POZITIF_KELIMELER = ["bullish", "price surge", "buy", "support", "pump", "positive", "gain", "rally", "green", "accumulate", "all-time high", "optimistic"]
# Hangi kelimeler olumsuz
NEGATIF_KELIMELER = ["bearish", "sell", "dump", "crash", "fear", "negative", "loss", "red", "panic", "plummet", "short", "decline"]

async def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                if resp.status != 200:
                    print(f"Telegram gönderim hatası: {await resp.text()}")
    except Exception as e:
        print(f"Telegram bağlantı hatası: {e}")

def haber_analiz(ozet):
    ozet = ozet.lower()
    pozitif_mi = any(kelime in ozet for kelime in POZITIF_KELIMELER)
    negatif_mi = any(kelime in ozet for kelime in NEGATIF_KELIMELER)

    if pozitif_mi and not negatif_mi:
        return "AL"
    elif negatif_mi and not pozitif_mi:
        return "SAT"
    else:
        return "NÖTR"

async def haberleri_tarama():
    while True:
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                baslik = entry.title
                ozet = entry.summary if hasattr(entry, 'summary') else ''
                link = entry.link
                zaman = entry.published if hasattr(entry, 'published') else datetime.datetime.now().isoformat()

                analiz_sonuc = haber_analiz(ozet + " " + baslik)

                if analiz_sonuc != "NÖTR":
                    for coin in COINLER:
                        if coin in baslik.upper() or coin in ozet.upper():
                            if analiz_sonuc == "AL":
                                mesaj = f"<b>{coin}</b> için alım fırsatı görüldü.\n{link}"
                            elif analiz_sonuc == "SAT":
                                mesaj = f"<b>{coin}</b> için satış fırsatı görüldü. SHORT işlem açılabilir.\n{link}"
                            await telegram_mesaj_gonder(mesaj)
                else:
                    for coin in COINLER:
                        if coin in baslik.upper() or coin in ozet.upper():
                            mesaj = f"<b>{coin}</b> için önemli bir etki beklenmiyor. Bekle.\n{link}"
                            await telegram_mesaj_gonder(mesaj)

        print(f"Haber taraması tamamlandı. 1 saat uykuya geçiliyor...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(haberleri_tarama())
