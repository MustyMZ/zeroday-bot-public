import os
import time
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands

# Ortam değişkenlerini yükle
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Binance ve Telegram bağlantısı
client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

# Parametreler
TIMEFRAME = "15m"
LIMIT = 150
RSI_LOW = 40
RSI_HIGH = 60

# BTC trendi
def get_btc_trend():
    try:
        btc_data = client.get_ticker(symbol="BTCUSDT")
        change = float(btc_data["priceChangePercent"])
        if change >= 1.25:
            return "UP"
        elif change <= -1.25:
            return "DOWN"
        else:
            return "SIDEWAYS"
    except:
        return "SIDEWAYS"

# Kline verisi çekme
def get_klines(symbol, interval=TIMEFRAME, limit=LIMIT):
    try:
        data = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(data, columns=[
            'time','open','high','low','close','volume','close_time',
            'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume','ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        return df
    except Exception as e:
        print(f"Kline verisi alınamadı: {symbol} - {e}")
        return None

# Teknik analiz ve sinyal üretimi
def analyze_symbol(symbol):
    if symbol not in valid_symbols:
        return

    df = get_klines(symbol)
    if df is None or df.empty:
        return

    print(f"Analiz başlatıldı: {symbol}")

    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd = MACD(df['close'])
    macd_line = macd.macd().iloc[-1]
    macd_signal = macd.macd_signal().iloc[-1]
    macd_hist = macd.macd_diff().iloc[-1]

    last = df.iloc[-1]
    prev = df.iloc[-2]
    if prev['volume'] == 0:
        return

    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100
    df['ema14'] = df['close'].ewm(span=14).mean()
    df['ema28'] = df['close'].ewm(span=28).mean()
    trend_up = df['ema14'].iloc[-1] > df['ema28'].iloc[-1]
    trend_down = df['ema14'].iloc[-1] < df['ema28'].iloc[-1]
    btc_trend = get_btc_trend()

    adx = ADXIndicator(df['high'], df['low'], df['close'], window=14).adx().iloc[-1]
    bb = BollingerBands(df['close'], window=20, window_dev=2)
    bb_signal = df['close'].iloc[-1] < bb.bollinger_l_hband().iloc[-1]

    buy_signal = (
        rsi < RSI_LOW and
        macd_hist > 0 and
        macd_line > macd_signal and
        trend_up and
        volume_change > 15 and
        adx > 15 and
        bb_signal
    )

    sell_signal = (
        rsi > RSI_HIGH and
        macd_hist < 0 and
        macd_line < macd_signal and
        trend_down and
        volume_change > 15 and
        adx > 15
    )

    print(f"BUY: {buy_signal} | SELL: {sell_signal} | RSI: {rsi} | MACD: {macd_hist} | Volume: {volume_change}")
    if buy_signal or sell_signal:
        direction = "BUY" if buy_signal else "SELL"
        confidence = "GÜÇLÜ" if volume_change > 40 else "NORMAL"

        entry_price = float(df['close'].iloc[-1])
        sl_price = entry_price * 0.98
        tp_price = entry_price * 1.03

        message = (
            f"🟦UZUN VADEAN!!! {direction} Sinyali: Hareket Zamanı\n"
            f"Coin: {symbol}\n"
            f"RSI: {round(rsi, 2)} | MACD: {round(macd_hist, 4)}\n"
            f"Hacim Değişimi: %{round(volume_change, 2)}\n"
            f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'} | BTC: {btc_trend}\n"
            f"Güven: {confidence}\n"
            f"Giriş: {round(entry_price, 4)} | TP: {round(tp_price, 4)} | SL: {round(sl_price, 4)}\n"
            f"(Dry-run mod: Gerçek emir gönderilmedi)"
        )

        send_telegram_message(message)

# Telegram mesaj fonksiyonu
def send_telegram_message(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

# Coin listesini hacme göre al
def get_top_symbols(limit=200):
    info = client.futures_exchange_info()
    tickers = client.futures_ticker()
    valid = {
        s['symbol'] for s in info['symbols']
        if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT'
    }
    symbols_with_volume = [
        (t['symbol'], float(t['quoteVolume']))
        for t in tickers if t['symbol'] in valid
    ]
    sorted_symbols = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
    return [s[0] for s in sorted_symbols[:limit]]

# Sembol listesi güncelle
valid_symbols = get_top_symbols()
print(f"Sembol sayısı: {len(valid_symbols)}")

# Sonsuz döngü
while True:
    for symbol in valid_symbols:
        try:
            analyze_symbol(symbol)
        except Exception as e:
            print(f"Hata ({symbol}): {e}")
    time.sleep(60)