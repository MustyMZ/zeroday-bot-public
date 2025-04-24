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

    # Alım stratejisi: Fiyat 40,000 USD'yi geçtiğinde al
    if last_price > 40000:
        print(f"Fiyat {last_price} > 40,000! BTC al!")
        buy_btc(0.001)  # 0.001 BTC almayı deneyelim (örnek miktar)
    
    # Satış stratejisi: Fiyat 45,000 USD'yi geçtiğinde sat
    if last_price > 45000:
        print(f"Fiyat {last_price} > 45,000! BTC sat!")
        sell_btc(0.001)  # 0.001 BTC satmayı deneyelim (örnek miktar)

# Botu başlatma fonksiyonu
def run_bot():
    print("ZER0DAY bot çalışıyor...")
    while True:
        turtle_trading_strategy()  # Stratejiyi sürekli çalıştırıyoruz
        print("Market kontrol ediliyor...")
        time.sleep(10)  # 10 saniyede bir market kontrolü yapılır

# Ana fonksiyon çalıştırma
if __name__ == "__main__":
    run_bot()
