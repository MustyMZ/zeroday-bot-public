import telegram
import time
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_API_SECRET
from binance.client import Client

# Binance API bağlantısı
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Telegram mesaj gönderme
def send_telegram_message(message):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Telegram mesajı gönderildi!")
    except Exception as e:
        print(f"Telegram Hatası: {e}")

# Coin analiz fonksiyonu
def analyze_coin(symbol, high_threshold, low_threshold):
    try:
        market_data = client.get_ticker(symbol=symbol)
        price = float(market_data['lastPrice'])
        print(f"{symbol} Fiyatı: {price}")

        if price > high_threshold:
            send_telegram_message(f"{symbol} için AL: {price} > {high_threshold}")
        elif price < low_threshold:
            send_telegram_message(f"{symbol} için SAT: {price} < {low_threshold}")
        else:
            print(f"{symbol}: Fiyat aralıkta, işlem yok.")
    except Exception as e:
        print(f"{symbol} analiz hatası: {e}")

# Coin listesi ve eşik değerleri
watchlist = {
    "BTCUSDT": {"high": 95000, "low": 90000},
    "ETHUSDT": {"high": 5000, "low": 4500},
    "SOLUSDT": {"high": 200, "low": 170}
    # buraya istediğin kadar coin ekleyebilirsin
}

# Bot başlatma
def run_bot():
    print("ZER0DAY çoklu coin bot çalışıyor...")
    send_telegram_message("ZER0DAY bot çalışmaya başladı!")

    while True:
        for symbol, levels in watchlist.items():
            analyze_coin(symbol, levels["high"], levels["low"])
        print("Tüm coinler kontrol edildi. 60 sn bekleniyor...\n")
        time.sleep(60)

# Çalıştır
if __name__ == "__main__":
    run_bot()
