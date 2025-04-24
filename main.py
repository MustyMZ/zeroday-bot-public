import telegram
import time
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from binance.client import Client

# Binance API Key ve Secret
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Telegram mesaj gönderme fonksiyonu
def send_telegram_message(message):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Telegram mesajı gönderildi!")
    except Exception as e:
        print(f"Hata: {e}")

# Ticaret stratejisi (Turtle Trading örneği)
def turtle_trading_strategy():
    market_data = client.get_ticker(symbol='BTCUSDT')
    print(f"Market verisi alındı: {market_data}")
    last_price = float(market_data['lastPrice'])

    # Alım ve Satım stratejileri
    if last_price > 45000:  # Fiyat 45,000 USDT'den yüksekse alım yap
        print(f"Fiyat {last_price} > 45,000, alım yapılıyor.")
        send_telegram_message(f"Alım yapılıyor: {last_price} > 45,000")
        # buy_btc(0.001)  # Alım işlemi yapılacak miktar
    if last_price < 40000:  # Fiyat 40,000 USDT'den düşükse satım yap
        print(f"Fiyat {last_price} < 40,000, satım yapılıyor.")
        send_telegram_message(f"Satım yapılıyor: {last_price} < 40,000")
        # sell_btc(0.001)  # Satım işlemi yapılacak miktar

# Botu çalıştırma
def run_bot():
    print("ZER0DAY bot çalışıyor...")
    
    # Telegram mesajını gönderelim bot başlar başlamaz
    send_telegram_message("Bot çalışmaya başladı!")
    
    while True:
        turtle_trading_strategy()  # Stratejiyi sürekli çalıştırıyoruz
        print("Market kontrol ediliyor...")
        time.sleep(60)  # 1 dakikada bir market kontrolü yapılır

# Botu başlat
run_bot()
import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Telegram mesajı gönderildi!")
    except Exception as e:
        print(f"Hata: {e}")

# Test mesajını gönderelim
send_telegram_message("Test: Telegram'a mesaj gönderildi!")
