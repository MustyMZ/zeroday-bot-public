import os
import time
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD
from telegram import Bot
from dotenv import load_dotenv

# Ortam değişkenlerini yükle (.env dosyasından)
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

# Binance Futures'taki geçerli coin listesini al
valid_symbols = [
    item['symbol'] for item in client.futures_exchange_info()['symbols']
    if item['contractType'] == 'PERPETUAL' and item['quoteAsset'] == 'USDT'
]

# Hacme göre sıralayıp ilk 200 coin'i seç
volume_info = client.futures_ticker()
symbols_with_volume = [
    (item['symbol'], float(item['quoteVolume']))
    for item in volume_info if item['symbol'] in valid_symbols
]
symbols_sorted = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
SYMBOLS = [s[0] for s in symbols_sorted[:200]]

def get_klines(symbol):
    try:
        data = client.futures_klines(symbol=symbol, interval="15m", limit=100)
        df = pd.DataFrame(data, columns=[
            'time','open','high','low','close','volume',
            'close_time','qav','num_trades','tbbav','tbqav','ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    except:
        return None

def send_signal(symbol, direction, rsi, macd, volume_change):
    message = (
        "KRİTİK Sinyal Geldi [{}]:\n"
        "Coin: {}\n"
        "RSI: {:.2f}\n"
        "MACD: {:.5f}\n"
        "Hacim Değişimi: {:.2f}%"
    ).format(direction.upper(), symbol, rsi, macd, volume_change)
    bot.send_message(chat_id=CHAT_ID, text=message)

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return

    rsi_series = RSIIndicator(df['close']).rsi()
    macd_line = MACD(df['close']).macd()
    signal_line = MACD(df['close']).macd_signal()

    rsi = rsi_series.iloc[-1]
    prev_rsi = rsi_series.iloc[-2]
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    prev_macd = macd_line.iloc[-2]
    prev_signal = signal_line.iloc[-2]

    vol = df['volume']
    volume_change = ((vol.iloc[-1] - vol.iloc[-2]) / vol.iloc[-2]) * 100

    # BUY sinyali (dipten dönüş)
    if 30 <= rsi <= 40 and rsi > prev_rsi and macd_val > signal_val and prev_macd <= prev_signal and volume_change > 0:
        send_signal(symbol, "BUY", rsi, macd_val, volume_change)

    # SELL sinyali (pump sonrası düşüş başlıyor)
    elif rsi >= 70 and rsi < prev_rsi and macd_val < signal_val and prev_macd >= prev_signal and volume_change < 0:
        send_signal(symbol, "SELL", rsi, macd_val, volume_change)

# Ana döngü (her 5 dakikada bir tarar)
while True:
    for symbol in SYMBOLS:
        try:
            analyze_symbol(symbol)
        except Exception as e:
            print(f"HATA: {symbol} - {e}")
    time.sleep(300)  # 5 dakika bekle