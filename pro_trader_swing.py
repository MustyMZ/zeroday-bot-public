import os
import ccxt
import pandas as pd
import numpy as np
import ta
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LIVE_MODE = os.getenv("LIVE_MODE", "False") == "True"

exchange = ccxt.binance()
markets = exchange.load_markets()

MAX_OPEN_TRADES = 3
MAX_POSITION_SIZE = 100

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def get_ohlcv(symbol, timeframe='15m', limit=50):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception as e:
        print(f"HATA OHLCV: {symbol} {e}")
        return []

def calculate_indicators(df):
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    df['ema14'] = ta.trend.EMAIndicator(close, window=14).ema_indicator()
    df['ema28'] = ta.trend.EMAIndicator(close, window=28).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()
    return df

def analyze(symbol):
    if '/USDT' not in symbol or 'UP' in symbol or 'DOWN' in symbol:
        return

    ohlcv = get_ohlcv(symbol)
    if not ohlcv or len(ohlcv) < 30:
        return

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = calculate_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    rsi = last['rsi']
    macd_hist = last['macd_hist']
    macd_signal = last['macd']
    macd_trigger = last['macd_signal']
    ema14 = last['ema14']
    ema28 = last['ema28']
    atr = last['atr']
    close_price = last['close']
    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100

    trend_up = ema14 > ema28
    trend_down = ema14 < ema28
    macd_buy = macd_hist > 0 and macd_signal > macd_trigger
    macd_sell = macd_hist < 0 and macd_signal < macd_trigger

    buy_signal = rsi < 40 and macd_buy and trend_up and volume_change > 40
    sell_signal = rsi > 70 and macd_sell and trend_down and volume_change > 40

    tp_percent = 6 if buy_signal else 4
    sl_percent = 2

    signal_strength = "GÃÃLÃ" if volume_change > 50 and ((buy_signal and rsi < 30) or (sell_signal and rsi > 75)) else "NORMAL"
    action = "BUY" if buy_signal else "SELL" if sell_signal else None

    if action:
        tp_price = close_price * (1 + tp_percent / 100) if action == "BUY" else close_price * (1 - tp_percent / 100)
        sl_price = close_price * (1 - sl_percent / 100) if action == "BUY" else close_price * (1 + sl_percent / 100)

        msg = f"[SÄ°NYAL: {signal_strength} {action}]\n"
        msg += f"Coin: {symbol}\n"
        msg += f"Fiyat: {close_price:.4f}\n"
        msg += f"RSI: {rsi:.2f} | MACD: {'YUKARI' if macd_buy else 'AÅAÄI'}\n"
        msg += f"Hacim DeÄiÅimi: %{volume_change:.2f}\n"
        msg += f"Trend: {'YUKARI' if trend_up else 'AÅAÄI'}\n"
        msg += f"TP: %{tp_percent:.1f} ({tp_price:.4f}) | SL: %{sl_percent:.1f} ({sl_price:.4f})\n"
        msg += f"Durum: {'GERÃEK EMÄ°R' if LIVE_MODE else 'TEST MODU'}"

        send_telegram(msg)

while True:
    usdt_markets = [s for s in markets if "/USDT" in s and ":USDT" not in s and "1000" not in s]
    for symbol in usdt_markets[:100]:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)