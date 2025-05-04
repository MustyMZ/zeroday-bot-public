import os
import time
import asyncio
import pandas as pd
from binance.client import Client
from binance.enums import *
from ta.momentum import RSIIndicator
from ta.trend import MACD
from telegram import Bot
from dotenv import load_dotenv
load_dotenv()

# API anahtarları
binance_api_key = os.getenv("BINANCE_API_KEY")
binance_api_secret = os.getenv("BINANCE_API_SECRET")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(binance_api_key, binance_api_secret)
bot = Bot(token=telegram_token)

# Coin listesi ve ayarlar
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "AVAXUSDT",
         "DOGEUSDT", "MATICUSDT", "PEPEUSDT", "ARBUSDT", "OPUSDT"]

INTERVAL = Client.KLINE_INTERVAL_15MINUTE
LIMIT = 100
MAX_POSITION_USDT = 100

async def send_telegram_message(message):
    await bot.send_message(chat_id=telegram_chat_id, text=message)

def get_ohlcv(symbol, interval, limit):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

def analyze(df):
    rsi = RSIIndicator(df['close'], window=14).rsi()
    macd_line = MACD(df['close']).macd()
    signal_line = MACD(df['close']).macd_signal()
    last_rsi = rsi.iloc[-1]
    last_macd = macd_line.iloc[-1]
    last_signal = signal_line.iloc[-1]

    last_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].iloc[-6:-1].mean()
    volume_confirmed = last_volume > avg_volume

    signal = None
    leverage = 5
    tp_pct = 0
    sl_pct = 0

    if last_rsi < 30 and last_macd > last_signal and volume_confirmed:
        signal = "BUY"
        leverage = 15 if last_rsi < 20 else 10
        tp_pct = 0.04
        sl_pct = 0.02
    elif last_rsi > 70 and last_macd < last_signal and volume_confirmed:
        signal = "SELL"
        leverage = 15 if last_rsi > 80 else 10
        tp_pct = 0.04
        sl_pct = 0.02

    return signal, last_rsi, last_macd, last_signal, volume_confirmed, leverage, tp_pct, sl_pct

async def main_loop():
    while True:
        for symbol in COINS:
            try:
                df = get_ohlcv(symbol, INTERVAL, LIMIT)
                signal, rsi, macd, macd_signal, vol_conf, lev, tp, sl = analyze(df)

                # Log ekran çıktısı
                print(f"\n--- {symbol} ---")
                print(f"RSI: {rsi:.2f} | MACD: {macd:.2f} / Signal: {macd_signal:.2f}")
                print(f"Hacim teyidi: {'EVET' if vol_conf else 'HAYIR'}")
                print(f"Sinyal: {signal if signal else 'YOK'}")

                if signal:
                    message = (
                        f"{symbol} - Sinyal: {signal}\n"
                        f"RSI: {rsi:.2f} | MACD: {macd:.2f} / Signal: {macd_signal:.2f}\n"
                        f"Hacim teyidi: {'EVET' if vol_conf else 'HAYIR'}\n"
                        f"Kaldıraç: {lev}x | Pozisyon: {MAX_POSITION_USDT}$\n"
                        f"TP: {tp*100:.1f}% | SL: {sl*100:.1f}%\n"
                        f"(Dry-run mod: Gerçek emir gönderilmedi)"
                    )
                    await send_telegram_message(message)
                    print("Telegram mesajı gönderildi:", message)

            except Exception as e:
                print(f"{symbol} için analiz hatası:", str(e))

        time.sleep(15)  # test modu için 15 saniye aralık

if __name__ == "__main__":
    asyncio.run(main_loop())