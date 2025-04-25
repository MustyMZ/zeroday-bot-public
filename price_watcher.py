# price_watcher.py
import time
from binance.client import Client
import pandas as pd

API_KEY = 'BINANCE_API_KEY'
API_SECRET = 'BINANCE_SECRET_KEY'
client = Client(API_KEY, API_SECRET)

def get_latest_price(symbol):
    try:
        data = client.get_klines(symbol=symbol, interval='1m', limit=2)
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df['close'].iloc[-2], df['close'].iloc[-1]
    except Exception as e:
        return None, None

def detect_spike(symbol="BTCUSDT", threshold=1.0):
    old_price, new_price = get_latest_price(symbol)
    if old_price is None or new_price is None:
        return f"{symbol} fiyat verisi alınamadı."
    
    change_percent = ((new_price - old_price) / old_price) * 100
    if abs(change_percent) >= threshold:
        return f"{symbol} ANI HAREKET: {change_percent:.2f}%"
    else:
        return f"{symbol} stabil: {change_percent:.2f}%"

# test
if __name__ == "__main__":
    while True:
        print(detect_spike("BTCUSDT"))
        time.sleep(60)
