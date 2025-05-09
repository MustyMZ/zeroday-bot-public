import os
import time
import pandas as pd
from binance.client import Client
from telegram import Bot
from dotenv import load_dotenv
from ta.momentum import RSIIndicator
from ta.trend import MACD

# Ortam değişkenlerini yükle
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Binance ve Telegram bağlantısı
client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

# Geçerli coin listesini çek (PERPETUAL + USDT)
valid_symbols = [
    item['symbol']
    for item in client.futures_exchange_info()['symbols']
    if item['contractType'] == 'PERPETUAL' and item['quoteAsset'] == 'USDT'
]

# Hacme göre sıralama ve ilk 200 coin seçimi
volume_info = client.futures_ticker()
symbols_with_volume = [
    (item['symbol'], float(item['quoteVolume']))
    for item in volume_info
    if item['symbol'] in valid_symbols
]
symbols_sorted = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
SYMBOLS = [s[0] for s in symbols_sorted[:200]]

# Parametreler
TIMEFRAME = "15m"
LIMIT = 150
RSI_LOW = 35
RSI_HIGH = 65

def get_btc_trend():
    btc_data = client.get_ticker(symbol="BTCUSDT")
    change = float(btc_data["priceChangePercent"])
    if change >= 1.25:
        return "UP"
    elif change <= -1.25:
        return "DOWN"
    else:
        return "SIDEWAYS"

def get_klines(symbol):
    data = client.get_klines(symbol=symbol, interval=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(data, columns=[
        'time','open','high','low','close','volume','close_time',
        'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume','ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

def send_signal(symbol, direction, rsi, macd, volume_change):
    message = (
        "KRİTİK AN! {} Sinyali: Hareket Zamanı\n"
        "Coin: {}\n"
        "RSI: {:.2f}\n"
        "MACD: {:.5f}\n"
        "Hacim Değişimi: {:.2f}%"
    ).format(direction.upper(), symbol, rsi, macd, volume_change)

    bot.send_message(chat_id=CHAT_ID, text=message)

def analyze_symbol(symbol):
    if symbol not in valid_symbols:
        return

    df = get_klines(symbol)
    if df is None or df.empty:
        return

    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    prev_rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-2]
    macd_line = MACD(df['close']).macd().iloc[-1]
    macd_signal = MACD(df['close']).macd_signal().iloc[-1]
    prev_macd_line = MACD(df['close']).macd().iloc[-2]
    prev_macd_signal = MACD(df['close']).macd_signal().iloc[-2]

    vol = df['volume']
    vol_change = ((vol.iloc[-1] - vol.iloc[-2]) / vol.iloc[-2]) * 100
    vol_trend = vol.iloc[-3] < vol.iloc[-2] < vol.iloc[-1]

    direction = None

    # BUY (dipten dönüş + zamanlama)
    if prev_rsi < rsi < 40 and macd_line > macd_signal and prev_macd_line <= prev_macd_signal and vol_trend:
        direction = "BUY"

    # SELL (tepe zayıflaması + zamanlama)
    elif prev_rsi > rsi > 65 and macd_line < macd_signal and prev_macd_line >= prev_macd_signal and not vol_trend:
        direction = "SELL"

    if direction:
        send_signal(symbol, direction, rsi, macd_line, vol_change)

# Sürekli tarama döngüsü
while True:
    for symbol in SYMBOLS:
        try:
            analyze_symbol(symbol)
        except Exception as e:
            print(f"Hata: {symbol} - {e}")
    time.sleep(60)