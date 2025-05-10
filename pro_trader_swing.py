import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD
from telegram import Bot

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

valid_symbols = [
    item['symbol'] for item in client.futures_exchange_info()['symbols']
    if item['contractType'] == 'PERPETUAL' and item['status'] == 'TRADING'
]

volume_info = client.futures_ticker()
symbols_with_volume = [
    (item['symbol'], float(item['quoteVolume']))
    for item in volume_info
    if item['symbol'] in valid_symbols
]

symbols_sorted = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
SYMBOLS = [s[0] for s in symbols_sorted[:200]]

TIMEFRAME = "15m"

def get_klines(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval=TIMEFRAME, limit=100)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    except Exception as e:
        print(f"Klines hatası: {symbol} – {e}")
        return None

def send_signal(symbol, direction, rsi, macd, volume_change):
    message = (
        f"KRA*TİK S*NYAL – [{direction}]\n"
        f"Coin: {symbol}\n"
        f"RSI: {rsi:.2f}\n"
        f"MACD: {macd:.5f}\n"
        f"Hacim Değişimi: %{volume_change:.2f}"
    )
    bot.send_message(chat_id=CHAT_ID, text=message)

def analyze_symbol(symbol):
    if symbol not in valid_symbols:
        return

    df = get_klines(symbol)
    if df is None or df.empty:
        return

    close = df['close']
    vol = df['volume']
    rsi = RSIIndicator(close).rsi().iloc[-1]
    macd_line = MACD(close).macd().iloc[-1]
    macd_signal = MACD(close).macd_signal().iloc[-1]
    volume_change = ((vol.iloc[-1] - vol.iloc[-2]) / vol.iloc[-2]) * 100 if vol.iloc[-2] != 0 else 0

    if rsi < 40 and macd_line > macd_signal and volume_change > 40:
        send_signal(symbol, "BUY", rsi, macd_line, volume_change)

    elif rsi > 60 and macd_line < macd_signal and volume_change > 40:
        send_signal(symbol, "SELL", rsi, macd_line, volume_change)

for symbol in SYMBOLS:
    analyze_symbol(symbol)