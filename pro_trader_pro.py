import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from binance.client import Client
from telegram import Bot
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

# Parametreler
TIMEFRAME = "15m"
LIMIT = 150

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

# BTC Dominance

def get_btc_dominance():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global")
        data = response.json()
        dominance = data["data"]["market_cap_percentage"]["btc"]
        return dominance
    except:
        return None

# ALTBTC Parite Gücü

def get_altbtc_strength(symbol):
    try:
        if not symbol.endswith("USDT"):
            return None
        base = symbol.replace("USDT", "")
        altbtc_symbol = base + "BTC"
        altbtc_klines = client.get_klines(symbol=altbtc_symbol, interval="15m", limit=5)
        closes = [float(k[4]) for k in altbtc_klines]
        return "GÜÇLÜ" if closes[-1] > closes[0] else "ZAYIF"
    except:
        return "BİLİNMİYOR"

# Funding Rate

def get_funding_rate(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        response = requests.get(url)
        data = response.json()
        rate = float(data[0]["fundingRate"]) * 100
        return rate
    except:
        return None

# Whale + Volume Spike

def detect_whale_volume_spike(df):
    try:
        volume_now = df['volume'].iloc[-1]
        volume_avg = df['volume'].iloc[-6:-1].mean()
        return volume_now > 2 * volume_avg
    except:
        return False

# Puanlama fonksiyonu (örnek olarak RSI verildi, diğerleri benzer mantıkla yapılmalı)

def score_rsi_buy(rsi):
    if rsi <= 30:
        return 100
    elif rsi <= 35:
        return 80
    elif rsi <= 40:
        return 60
    elif rsi <= 50:
        return 30
    else:
        return 0

def score_rsi_sell(rsi):
    if rsi >= 70:
        return 100
    elif rsi >= 65:
        return 80
    elif rsi >= 60:
        return 60
    elif rsi >= 55:
        return 30
    else:
        return 0

# Kline verisi

def get_klines(symbol, interval=TIMEFRAME, limit=LIMIT):
    try:
        data = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(data, columns=[
            'time','open','high','low','close','volume','close_time',
            'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume','ignore'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        return df
    except Exception as e:
        print(f"Kline verisi alınamadı: {symbol} - {e}")
        return None

# Teknik analiz ve puanlı sinyal

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return

    print(f"Analiz başlatıldı: {symbol}")

    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd = MACD(df['close'])
    macd_hist = macd.macd_diff().iloc[-1]
    macd_line = macd.macd().iloc[-1]
    macd_signal = macd.macd_signal().iloc[-1]

    last = df.iloc[-1]
    prev = df.iloc[-2]

    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100
    trend_up = df['close'].ewm(span=14).mean().iloc[-1] < df['close'].iloc[-1]
    trend_down = not trend_up
    btc_trend = get_btc_trend()
    btc_dominance = get_btc_dominance() or 50
    funding_rate = get_funding_rate(symbol) or 0
    altbtc_strength = get_altbtc_strength(symbol) if not symbol.startswith("BTC") else "GÜÇLÜ"
    if altbtc_strength == "BİLİNMİYOR":
        altbtc_strength = "ZAYIF"
    whale_volume_spike = detect_whale_volume_spike(df)

    is_buy = rsi < 50 and macd_hist > 0 and macd_line > macd_signal and trend_up
    is_sell = rsi > 50 and macd_hist < 0 and macd_line < macd_signal and trend_down

    score = 0
    if is_buy:
        score += score_rsi_buy(rsi)
        # Diğer puanlar burada toplanacak
    elif is_sell:
        score += score_rsi_sell(rsi)
        # Diğer puanlar burada toplanacak

    confidence = "ZAYIF"
    if score >= 200:
        confidence = "GÜÇLÜ"
    elif score >= 120:
        confidence = "NORMAL"

    if not is_buy and not is_sell:
        return

    direction = "BUY" if is_buy else "SELL"
    message = (
        f"📊 {direction} Sinyali\n"
        f"Coin: {symbol}\n"
        f"RSI: {round(rsi, 2)} | MACD: {round(macd_hist, 4)}\n"
        f"Hacim Değişimi: %{round(volume_change, 2)}\n"
        f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'} | BTC: {btc_trend}\n"
        f"BTC Dominance: %{round(btc_dominance, 2)}\n"
        f"ALTBTC Gücü: {altbtc_strength} | Funding: %{round(funding_rate, 4)}\n"
        f"Whale + Hacim Spike: {'VAR' if whale_volume_spike else 'YOK'}\n"
        f"Toplam Skor: {score} | Güven: {confidence}\n"
        f"(Dry-run mod: Gerçek emir gönderilmedi)"
    )
    send_telegram_message(message)

# Telegram mesajı

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

# Coin listesini hacme göre al

def get_top_symbols():
    info = client.futures_exchange_info()
    tickers = client.futures_ticker()
    valid = {
        s['symbol'] for s in info['symbols']
        if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT'
    }
    return [t['symbol'] for t in tickers if t['symbol'] in valid]

# Ana döngü
valid_symbols = get_top_symbols()
while True:
    for symbol in valid_symbols:
        try:
            analyze_symbol(symbol)
        except Exception as e:
            print(f"Hata ({symbol}): {e}")
    time.sleep(60)