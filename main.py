import asyncio
from binance.client import Client
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_API_SECRET

# Binance API bağlantısı
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Telegram bot nesnesi
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Telegram mesaj gönderme fonksiyonu (async)
async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Telegram mesajı gönderildi:", message)
    except Exception as e:
        print("Telegram Hatası:", e)

# Coin analiz fonksiyonu
async def analyze_coin(symbol, high_threshold, low_threshold):
    try:
        market_data = client.get_ticker(symbol=symbol)
        price = float(market_data["price"])
        print(f"{symbol} fiyatı: {price}")

        if price > high_threshold:
            await send_telegram_message(f"{symbol} için AL: {price} > {high_threshold}")
        elif price < low_threshold:
            await send_telegram_message(f"{symbol} için SAT: {price} < {low_threshold}")
        else:
            print(f"{symbol}: Fiyat aralıkta.")
    except Exception as e:
        print(f"{symbol} analiz hatası: {e}")

# İzlenecek coinler ve eşik değerleri
watchlist = {
    "BTCUSDT": {"high": 95000, "low": 90000},
    "ETHUSDT": {"high": 5000, "low": 4500},
    "SOLUSDT": {"high": 200, "low": 170}
}

# Bot çalıştırma döngüsü
async def run_bot():
    print("ZERODAY bot çalışıyor...")
    await send_telegram_message("ZERODAY bot çalışmaya başladı!")

    while True:
        tasks = [analyze_coin(symbol, values["high"], values["low"]) for symbol, values in watchlist.items()]
        await asyncio.gather(*tasks)
        print("Tüm coinler kontrol edildi. 60 saniye bekleniyor...\n")
        await asyncio.sleep(60)

# Başlat
if __name__ == "__main__":
    asyncio.run(run_bot())
