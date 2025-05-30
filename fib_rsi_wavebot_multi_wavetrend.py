import os
import time
import pandas as pd
import numpy as np
from binance.client import Client
from telegram import Bot
from dotenv import load_dotenv

# ENV yükle
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 200
TOLERANCE = 0.005

def get_futures_symbols():
    exchange_info = client.futures_exchange_info()
    usdt_symbols = [
        s['symbol'] for s in exchange_info['symbols']
        if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'
    ]
    return usdt_symbols

def get_klines(symbol):
    data = client.futures_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['low'] = df['low'].astype(float)
    df['high'] = df['high'].astype(float)
    return df

def fibonacci_levels(high, low):
    return {
        "38.2%": high - (high - low) * 0.382,
        "50.0%": high - (high - low) * 0.5,
        "61.8%": high - (high - low) * 0.618,
    }

def calculate_wave_trend(df, channel_length=10, average_length=21):
    close = df['close']
    esa = close.ewm(span=channel_length, adjust=False).mean()
    de = (abs(close - esa)).ewm(span=channel_length, adjust=False).mean()
    ci = (close - esa) / (0.015 * de)
    wt1 = ci.ewm(span=average_length, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_wave_cross(wt1, wt2):
    if len(wt1) < 2 or len(wt2) < 2:
        return "none"
    if wt1.iloc[-2] < wt2.iloc[-2] and wt1.iloc[-1] > wt2.iloc[-1]:
        return "bullish"
    elif wt1.iloc[-2] > wt2.iloc[-2] and wt1.iloc[-1] < wt2.iloc[-1]:
        return "bearish"
    return "none"

def analyze_coin(symbol):
    try:
        df = get_klines(symbol)
        high = df['high'].max()
        low = df['low'].min()
        last_price = df['close'].iloc[-1]
        fib = fibonacci_levels(high, low)
        wt1, wt2 = calculate_wave_trend(df)
        wave = get_wave_cross(wt1, wt2)

        for label, level in fib.items():
            if abs(last_price - level) / level < TOLERANCE:
                if wave == "bullish":
                    sl = low
                    tp = high
                    rr = round((tp - last_price) / (last_price - sl), 2)
                    send_signal("BUY", symbol, last_price, label, wave, sl, tp, rr)
                elif wave == "bearish":
                    sl = high
                    tp = low
                    rr = round((sl - last_price) / (tp - last_price), 2)
                    send_signal("SELL", symbol, last_price, label, wave, sl, tp, rr)
                break
    except Exception as e:
        print(f"Hata ({symbol}):", e)

def send_signal(signal_type, symbol, price, fib_label, wave, sl, tp, rr):
    message = f"""
🚀 {signal_type} Signal! [KESKİN NİŞANCI]
Coin: {symbol}
Price: {price:.4f}
Fib Level: {fib_label} yakınında
WaveCross: {wave.capitalize()}
Timeframe: 5m
Stop Loss: {sl:.4f}
Take Profit: {tp:.4f}
Risk/Reward: 1:{rr}

📌 Disiplinli kal. Haberleri takip et. Performansı düzenli gözden geçir.
"""
    bot.send_message(chat_id=CHAT_ID, text=message.strip())

if __name__ == "__main__":
    while True:
        try:
            symbols = get_futures_symbols()
            print(f"{len(symbols)} coin taranıyor...")
            for sym in symbols:
                if sym.endswith("USDT"):
                    analyze_coin(sym)
            print("Taramalar tamamlandı. 5 dk bekleniyor...\n")
        except Exception as err:
            print("Genel hata:", err)
        time.sleep(300)