import os
import time
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from binance.client import Client
from telegram import Bot
from dotenv import load_dotenv

# Yükle .env verileri
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Binance ve Telegram bağlantıları
client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

# Geçerli Futures coinleri al (PERPETUAL ve USDT olanlar)
exchange_info = client.futures_exchange_info()
valid_symbols = [s['symbol'] for s in exchange_info['symbols']
                 if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT']

# En yüksek hacimli 200 coin
volume_info = client.futures_ticker()
symbols_with_volume = [
    (item['symbol'], float(item['quoteVolume']))
    for item in volume_info if item['symbol'] in valid_symbols
]
symbols_sorted = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
SYMBOLS = [s[0] for s in symbols_sorted[:200]]

# Coin bazlı veri çekme fonksiyonu
def get_klines(symbol):
    data = client.futures_klines(symbol=symbol, interval="15m", limit=30)
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qav', 'not', 'tbbav', 'tbqav', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

# BUY/SELL kararı
def analyze_symbol(symbol):
    try:
        df = get_klines(symbol)
        rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
        macd = MACD(df['close']).macd().iloc[-1]
        signal = MACD(df['close']).macd_signal().iloc[-1]
        volume_now = df['volume'].iloc[-1]
        volume_prev = df['volume'].iloc[-2]
        volume_before = df['volume'].iloc[-3]

        direction = None
        neden = ""

        # --- BUY KARARI ---
        if (
            rsi < 40 and rsi > df['rsi'][-2] and
            macd > signal and
            volume_prev < volume_now and volume_before < volume_prev
        ):
            direction = "BUY"
            neden = "RSI dipten çıkıyor, MACD pozitif kesişim, hacim artışı var"

        # --- SELL KARARI ---
        elif (
            rsi > 70 and rsi < df['rsi'][-2] and
            macd < signal and
            volume_prev > volume_now and volume_before > volume_prev
        ):
            direction = "SELL"
            neden = "RSI tepeden düşüyor, MACD negatife geçiyor, hacim azalıyor"

        if direction:
            send_signal(symbol, direction, rsi, macd, volume_now, neden)
    except Exception as e:
        print(f"{symbol} analiz hatası: {e}")

# Telegram mesajı
def send_signal(symbol, direction, rsi, macd, volume, neden):
    mesaj = (
        f"[PROFESYONEL SİNYAL]\n"
        f"Coin: {symbol}\n"
        f"İşlem: {direction}\n"
        f"RSI: {rsi:.2f} | MACD: {macd:.5f}\n"
        f"Hacim: {volume:.2f}\n"
        f"Açıklama: {neden}\n"
        f"Kaynak: pro_trader_pro.py"
    )
    bot.send_message(chat_id=CHAT_ID, text=mesaj)

# Ana döngü
def main():
    for symbol in SYMBOLS:
        analyze_symbol(symbol)
        time.sleep(1)

if __name__ == "__main__":
    main()