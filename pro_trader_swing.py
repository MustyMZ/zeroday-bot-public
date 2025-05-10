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

valid_symbols = [item['symbol'] for item in client.futures_exchange_info()['symbols']
                 if item['contractType'] == 'PERPETUAL' and item['quoteAsset'] == 'USDT']

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
    data = client.get_klines(symbol=symbol, interval=TIMEFRAME, limit=100)
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

def send_signal(symbol, direction, rsi, macd, volume_change):
    message = (
    "KRİTİK SİNYAL – [{}]\n"
    "Coin: {}\n"
    "RSI: {:.2f}\n"
    "MACD: {:.5f}\n"
    "Hacim Değişimi: %{:.2f}"
    ).format(direction, symbol, rsi, macd, volume_change)
    bot.send_message(chat_id=CHAT_ID, text=message)

def analyze_symbol(symbol):
    if symbol not in valid_symbols:
        return

    df = get_klines(symbol)
    if df is None or df.empty:
        return

    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd_line = MACD(df['close']).macd().iloc[-1]

    vol = df['volume']
    if vol.iloc[-2] == 0 or pd.isna(vol.iloc[-2]):
        volume_change = 0
    else:
        volume_change = ((vol.iloc[-1] - vol.iloc[-2]) / vol.iloc[-2]) * 100

    direction = None
    if rsi < 40 and macd_line > 0 and volume_change > 40:
        direction = "BUY"
    elif rsi > 70 and macd_line < 0 and volume_change < -20:
        direction = "SELL"

    if direction:
        send_signal(symbol, direction, rsi, macd_line, volume_change)

def main():
    for symbol in SYMBOLS:
        analyze_symbol(symbol)

if __name__ == "__main__":
    main()