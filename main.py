import time
from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET

# Binance API bağlantısı
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Market bilgisi almak
def get_account_info():
    info = client.get_account()
    print(info)

# Örnek işlem: Balans (Bakiyeleri çekmek)
def get_balance():
    balance = client.get_asset_balance(asset='USDT')
    print(f"USDT Bakiyesi: {balance['free']}")

# Buy BTC Fonksiyonu
def buy_btc(amount):
    order = client.order_market_buy(
        symbol='BTCUSDT',  # BTC/USDT paritesinde işlem yapıyoruz
        quantity=amount     # Almak istediğimiz BTC miktarı
    )
    print(f"Buy order placed: {order}")

# Sell BTC Fonksiyonu
def sell_btc(amount):
    order = client.order_market_sell(
        symbol='BTCUSDT',  # BTC/USDT paritesinde işlem yapıyoruz
        quantity=amount     # Satmak istediğimiz BTC miktarı
    )
    print(f"Sell order placed: {order}")

# Turtle Trading Stratejisi
def turtle_trading_strategy():
    # Binance üzerinden BTC/USDT ticaret verisini al
    market_data = client.get_ticker(symbol='BTCUSDT')
    print(f"Market verisi alındı: {market_data}")
    
    last_price = float(market_data['lastPrice'])

    # Son 20 günün yüksek ve düşük fiyatlarını almak (bu veriyi gerçek zamanlı çekmeliyiz)
    highest_20 = 48000  # Örnek: Son 20 günün en yüksek fiyatı (bu veriyi gerçek zamanlı çekmeliyiz)
    lowest_20 = 40000    # Örnek: Son 20 günün en düşük fiyatı (bu veriyi gerçek zamanlı çekmeliyiz)

    # Alım Stratejisi: Fiyat son 20 günün yüksek fiyatına ulaşırsa alım yap
    if last_price > highest_20:
        print(f"Fiyat {last_price} > 20 günlük yüksek fiyatı: {highest_20}! BTC al!")
        buy_btc(0.001)  # 0.001 BTC almayı deneyelim (örnek miktar)
    
    # Satış Stratejisi: Fiyat son 20 günün düşük fiyatına ulaşırsa satış yap
    if last_price < lowest_20:
        print(f"Fiyat {last_price} < 20 günlük düşük fiyatı: {lowest_20}! BTC sat!")
        sell_btc(0.001)  # 0.001 BTC satmayı deneyelim (örnek miktar)

# Botu başlatma fonksiyonu
def run_bot():
    print("ZER0DAY bot çalışıyor...")
    while True:
        turtle_trading_strategy()  # Stratejiyi sürekli çalıştırıyoruz
        print("Market kontrol ediliyor...")
        time.sleep(60)  # 1 dakikada bir market kontrolü yapılır

# Ana fonksiyon çalıştırma
if __name__ == "__main__":m
    run_bot()
import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Telegram botunu başlatma
def send_telegram_message(message):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Ana fonksiyon çalıştırma
if _name_ == "_main_":
    send_telegram_message("Bot çalışıyor...")
import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
