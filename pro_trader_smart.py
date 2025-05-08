# API Anahtarları ve Bağlantılar
import os
import time
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.trend import MACD

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

# Binance Futures'taki geçerli coin listesi
exchange_info = client.futures_exchange_info()
valid_symbols = [
    item['symbol'] for item in exchange_info['symbols']
    if item['contractType'] == 'PERPETUAL' and item['quoteAsset'] == 'USDT'
]

# Hacme göre sıralama (sadece geçerli coinler)
volume_info = client.futures_ticker()
symbols_with_volume = [
    (item['symbol'], float(item['quoteVolume']))
    for item in volume_info
    if item['symbol'] in valid_symbols
]

symbols_sorted = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
SYMBOLS = [s[0] for s in symbols_sorted[:200]]

# Teknik analiz parametreleri
TIMEFRAME = "15m"
LIMIT = 150
RSI_LOW = 35
RSI_HIGH = 65
BTC_TREND_LIMIT = 1.25

def get_btc_trend():
    btc_data = client.get_ticker(symbol="BTCUSDT")
    change = float(btc_data["priceChangePercent"])
    if change >= BTC_TREND_LIMIT:
        return "UP"
    elif change <= -BTC_TREND_LIMIT:
        return "DOWN"
    else:
        return "SIDEWAYS"

def get_klines(symbol):
    data = client.get_klines(symbol=symbol, interval=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

def analyze_symbol(symbol, btc_trend):
    if symbol not in valid_symbols:
        return  # Binance'ta geçerli değilse işlemi atla
        
    df = get_klines(symbol)
    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd_line = MACD(df['close']).macd().iloc[-1]
    volume_change = (df['volume'].iloc[-1] - df['volume'].iloc[-2]) / df['volume'].iloc[-2] * 100

    direction = None
    sinyal_seviyesi = "ZAYIF"

    if btc_trend == "UP" and rsi > 40 and macd_line > 0.001 and volume_change > 40:
        direction = "BUY"
        sinyal_seviyesi = "YÜKSEK POTANSİYEL" if volume_change > 70 else "STANDART"
    elif btc_trend == "DOWN" and rsi > 60 and macd_line < -0.001 and volume_change > 40:
        direction = "SELL"
        sinyal_seviyesi = "YÜKSEK POTANSİYEL" if volume_change > 70 else "STANDART"
    elif btc_trend == "SIDEWAYS" and ((rsi < 30 and macd_line > 0.001) or (rsi > 70 and macd_line < -0.001)) and volume_change > 40:
        direction = "BUY" if rsi < 30 else "SELL"
        sinyal_seviyesi = "STANDART"

    if direction and sinyal_seviyesi != "ZAYIF":
        send_signal(symbol, direction, rsi, macd_line, volume_change, btc_trend, sinyal_seviyesi)

def send_signal(symbol, direction, rsi, macd, volume_change, btc_trend, seviye):
    title = f"[{seviye.upper()} SİNYAL]"
    mesaj = (
        f"{title}\n"
        f"Coin: {symbol}\n"
        f"İşlem: {direction}\n"
        f"BTC Trend: {btc_trend}\n"
        f"RSI: {rsi:.2f} | MACD: {macd:.5f}\n"
        f"Son Hacim Artışı: %{volume_change:.2f}\n"
        f"Tavsiye: {'GİRİLEBİLİR' if seviye != 'ZAYIF' else 'BEKLE'}\n"
        f"\nKaynak: PRO_TRADER_SMART"
    )
    bot.send_message(chat_id=CHAT_ID, text=mesaj)

def main():
    btc_trend = get_btc_trend()
    for symbol in SYMBOLS:
        try:
            analyze_symbol(symbol, btc_trend)
            time.sleep(1)
        except Exception as e:
            print(f"Hata: {symbol} - {e}")

if __name__ == "__main__":
    main()