# Protrader Pro (Güncellenmiş Sürüm)

import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from binance.client import Client
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from market_sentiment import get_market_sentiment_analysis
from scoring import (
    score_rsi, score_macd, score_volume_change, score_trend, score_btc_trend,
    score_btc_dominance, score_altbtc_strength, score_funding_rate, score_whale_spike,
    score_open_interest, score_long_short_ratio, score_taker_buy_sell, score_usdt_dominance,
    score_ema_cross, score_atr
)

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

# ProtraderPro - Göstergelere Dayalı Skorlama Sistemi

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# Skorlama fonksiyonları (BUY/SELL ayrımlı)
def score_rsi(rsi, direction):
    if direction == "BUY":
        if rsi <= 30: return 100
        elif rsi <= 35: return 90
        elif rsi <= 40: return 60
        elif rsi <= 50: return 30
        else: return 0
    elif direction == "SELL":
        if rsi >= 70: return 100
        elif rsi >= 65: return 80
        elif rsi >= 60: return 60
        elif rsi >= 55: return 30
        else: return 0

def score_macd(macd_hist, direction):
    if direction == "BUY":
        if macd_hist > 0.01: return 100
        elif macd_hist > 0.005: return 80
        elif macd_hist > 0.001: return 60
        elif macd_hist > 0: return 30
        else: return 0
    elif direction == "SELL":
        if macd_hist < -0.01: return 100
        elif macd_hist < -0.005: return 80
        elif macd_hist < -0.001: return 60
        elif macd_hist < 0: return 30
        else: return 0

def score_volume_change(volume_change, direction):
    if direction == "BUY":
        if volume_change > 100: return 100
        elif volume_change > 60: return 80
        elif volume_change > 30: return 60
        elif volume_change > 10: return 30
        else: return 10
    elif direction == "SELL":
        if volume_change < -100: return 100
        elif volume_change < -60: return 80
        elif volume_change < -30: return 60
        elif volume_change < -10: return 30
        else: return 10

def score_trend(trend_up, direction):
    return 100 if (trend_up and direction == "BUY") or (not trend_up and direction == "SELL") else 0

def score_btc_trend(trend, direction):
    if direction == "BUY":
        return 100 if trend == "UP" else 60 if trend == "SIDEWAYS" else 0
    elif direction == "SELL":
        return 100 if trend == "DOWN" else 60 if trend == "SIDEWAYS" else 0

def score_btc_dominance(dominance, direction):
    if direction == "BUY":
        if dominance < 49: return 100
        elif dominance < 53: return 80
        elif dominance < 57: return 60
        elif dominance < 60: return 30
        else: return 0
    elif direction == "SELL":
        if dominance > 63: return 100
        elif dominance > 61: return 80
        elif dominance > 58: return 60
        elif dominance > 56: return 30
        else: return 0

def score_altbtc_strength(strength):
    return 100 if strength == "GÜÇLÜ" else 0

def score_funding_rate(rate):
    if abs(rate) < 0.02: return 100
    elif abs(rate) < 0.05: return 80
    elif abs(rate) < 0.1: return 60
    elif abs(rate) < 0.25: return 30
    else: return 0

def score_whale_spike(spike):
    return 100 if spike else 0

def score_open_interest(oi):
    if oi > 20: return 100
    elif oi > 10: return 80
    elif oi > 5: return 60
    elif oi > 2: return 30
    else: return 0

def score_long_short_ratio(ratio, direction):
    if direction == "BUY":
        if ratio > 1.5: return 100
        elif ratio > 1.2: return 80
        elif ratio > 1.0: return 60
        elif ratio > 0.8: return 30
        else: return 0
    elif direction == "SELL":
        if ratio < 0.6: return 100
        elif ratio < 0.8: return 80
        elif ratio < 1.0: return 60
        elif ratio < 1.2: return 30
        else: return 0

def score_taker_buy_sell(ratio, direction):
    if direction == "BUY":
        if ratio > 1.1: return 100
        elif ratio > 1.0: return 80
        elif ratio > 0.95: return 60
        elif ratio > 0.9: return 30
        else: return 0
    elif direction == "SELL":
        if ratio < 0.9: return 100
        elif ratio < 0.95: return 80
        elif ratio < 1.0: return 60
        elif ratio < 1.05: return 30
        else: return 0

def score_usdt_dominance(dom):
    if dom > 6: return 100
    elif dom > 5: return 80
    elif dom > 4: return 60
    elif dom > 3: return 30
    else: return 0

def score_ema_cross(ema_fast, ema_slow, direction):
    distance = abs(ema_fast - ema_slow)
    percent_diff = (distance / ema_slow) * 100 if ema_slow > 0 else 0
    if direction == "BUY":
        if ema_fast > ema_slow and percent_diff >= 1.5: return 100
        elif ema_fast > ema_slow and percent_diff >= 1: return 80
        elif ema_fast > ema_slow and percent_diff >= 0.5: return 60
        elif ema_fast > ema_slow: return 30
        else: return 0
    elif direction == "SELL":
        if ema_fast < ema_slow and percent_diff >= 1.5: return 100
        elif ema_fast < ema_slow and percent_diff >= 1: return 80
        elif ema_fast < ema_slow and percent_diff >= 0.5: return 60
        elif ema_fast < ema_slow: return 30
        else: return 0

def score_atr(atr_percent):
    if atr_percent > 5: return 100
    elif atr_percent > 3: return 80
    elif atr_percent > 2: return 60
    elif atr_percent > 1: return 30
    else: return 0

def get_btc_trend():
    try:
        btc_data = client.get_ticker(symbol="BTCUSDT")
        change = float(btc_data["priceChangePercent"])
        if change >= 1.25: return "UP"
        elif change <= -1.25: return "DOWN"
        else: return "SIDEWAYS"
    except:
        return "SIDEWAYS"

def get_btc_dominance():
    try:
        res = requests.get("https://api.coingecko.com/api/v3/global")
        return res.json()["data"]["market_cap_percentage"]["btc"]
    except:
        return 50

def get_altbtc_strength(symbol):
    try:
        if not symbol.endswith("USDT"): return "ZAYIF"
        base = symbol.replace("USDT", "")
        altbtc = base + "BTC"
        data = client.get_klines(symbol=altbtc, interval="15m", limit=5)
        closes = [float(x[4]) for x in data]
        return "GÜÇLÜ" if closes[-1] > closes[0] else "ZAYIF"
    except:
        return "ZAYIF"

def get_funding_rate(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        data = requests.get(url).json()
        return float(data[0]["fundingRate"])*100
    except:
        return 0

def detect_whale_spike(df):
    try:
        now = df['volume'].iloc[-1]
        avg = df['volume'].iloc[-6:-1].mean()
        return now > 2 * avg
    except:
        return False

def get_klines(symbol, interval=TIMEFRAME, limit=LIMIT):
    try:
        data = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(data, columns=["time","open","high","low","close","volume",
                                         "close_time","qav","trades","tbav","tqav","ignore"])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    except:
        return None

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None: return

    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd_hist = MACD(df['close']).macd_diff().iloc[-1]
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if prev['volume'] == 0: return
    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100
    trend_up = df['close'].ewm(span=14).mean().iloc[-1] < df['close'].iloc[-1]
    btc_trend = get_btc_trend()
    btc_dominance = get_btc_dominance()
    funding_rate = get_funding_rate(symbol)
    altbtc_strength = get_altbtc_strength(symbol)
    whale_spike = detect_whale_spike(df)

    direction = "BUY" if rsi < 50 and macd_hist > 0 and trend_up else "SELL" if rsi > 50 and macd_hist < 0 and not trend_up else None
    if direction is None: return

total_score = (
    score_rsi(rsi, direction) +
    score_macd(macd_hist, direction) +
    score_volume_change(volume_change, direction) +
    score_trend(trend_up, direction) +
    score_btc_trend(btc_trend, direction) +
    score_btc_dominance(btc_dominance, direction) +
    score_altbtc_strength(altbtc_strength) +
    score_funding_rate(funding_rate) +
    score_whale_spike(whale_spike) +
    score_open_interest(oi) +
    score_long_short_ratio(ls_ratio, direction) +
    score_taker_buy_sell(taker_ratio, direction) +
    score_usdt_dominance(usdt_dom) +
    score_ema_cross(ema_fast, ema_slow, direction) +
    score_atr(atr_percent)
)

def analyze_symbol(symbol):
    ...
    confidence = "GÜÇLÜ" if total_score >= 700 else "NORMAL" if total_score >= 400 else "ZAYIF"
    if confidence == "ZAYIF":
        return
    ...

    message = (
        f"\n📊 {direction} Sinyali\nCoin: {symbol}\nRSI: {round(rsi, 2)}\nMACD: {round(macd_hist, 4)}\n"
        f"Hacim: %{round(volume_change, 2)}\nTrend: {'YUKARI' if trend_up else 'AŞAĞI'} | BTC Trend: {btc_trend}\n"
        f"BTC Dominance: %{btc_dominance} | ALTBTC: {altbtc_strength}\nFunding: %{round(funding_rate, 4)}\n"
        f"Whale Spike: {'VAR' if whale_spike else 'YOK'}\nToplam Skor: {total_score} | Güven: {confidence}"
    )

    try:
        sentiment_text, _ = get_market_sentiment_analysis(symbol, direction)
        full_message = message + "\n\n" + sentiment_text
        bot.send_message(chat_id=CHAT_ID, text=full_message)
    except:
        bot.send_message(chat_id=CHAT_ID, text=message)

# Tüm sembolleri al
symbols = [s['symbol'] for s in client.futures_exchange_info()['symbols'] if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT']

while True:
    for symbol in symbols:
        try:
            analyze_symbol(symbol)
        except Exception as e:
            print(f"Hata: {symbol} - {e}")
    time.sleep(60)