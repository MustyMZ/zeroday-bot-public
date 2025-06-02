# Protrader Pro (Güncellenmiş Sürüm + Yapay Zeka Yorumu)

import os
import time
import pandas as pd
import requests
import openai
from dotenv import load_dotenv
from binance.client import Client
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# Ortam değişkenlerini yükle
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

TIMEFRAME = "15m"
LIMIT = 150

def generate_ai_comment(symbol, rsi, macd_hist, volume_change, trend_up, btc_trend,
                         btc_dominance, funding_rate, whale_spike, open_interest,
                         ls_ratio, taker_ratio, usdt_dom, percent_diff, atr_percent,
                         total_score, confidence):
    try:
        prompt = f"""
Sen deneyimli bir kripto analistisin. Aşağıdaki verileri analiz ederek sadece bir cümlelik özet bir yorum yap:
- Coin: {symbol}
- RSI: {rsi}
- MACD: {macd_hist}
- Hacim Değişimi: %{volume_change}
- Trend: {'YUKARI' if trend_up else 'AŞAĞI'}
- BTC Trend: {btc_trend}
- BTC Dominance: %{btc_dominance}
- Funding Rate: %{funding_rate}
- Whale Spike: {'VAR' if whale_spike else 'YOK'}
- Open Interest: {open_interest}
- Long/Short Ratio: {ls_ratio}
- Taker Buy/Sell Ratio: {taker_ratio}
- USDT Dominance: %{usdt_dom}
- EMA Cross Fark: %{round(percent_diff, 2)}
- ATR: %{round(atr_percent, 2)}
- Toplam Skor: {total_score}
- Güven: {confidence}

Yorumun sade, net ve tek cümlelik olsun.
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI yorumu alınamadı: {e}"

def get_market_sentiment_analysis(symbol, direction):
    return "Sentiment verisi şu an kullanılamıyor.", None

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
        data = client.get_ticker(symbol="BTCUSDT")
        chg = float(data["priceChangePercent"])
        if chg >= 1.25: return "UP"
        elif chg <= -1.25: return "DOWN"
        else: return "SIDEWAYS"
    except: return "SIDEWAYS"

def get_btc_dominance():
    try:
        data = requests.get("https://api.coingecko.com/api/v3/global").json()
        return data["data"]["market_cap_percentage"]["btc"]
    except: return 50

def get_altbtc_strength(symbol):
    try:
        if not symbol.endswith("USDT"): return "ZAYIF"
        base = symbol.replace("USDT", "")
        alt = base + "BTC"
        data = client.get_klines(symbol=alt, interval="15m", limit=5)
        closes = [float(k[4]) for k in data]
        return "GÜÇLÜ" if closes[-1] > closes[0] else "ZAYIF"
    except: return "ZAYIF"

def get_funding_rate(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        data = requests.get(url).json()
        return float(data[0]["fundingRate"]) * 100
    except: return 0

def detect_whale_spike(df):
    try:
        now = df['volume'].iloc[-1]
        avg = df['volume'].iloc[-6:-1].mean()
        return now > 2 * avg
    except: return False

def get_klines(symbol, interval=TIMEFRAME, limit=LIMIT):
    try:
        data = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(data, columns=["time","open","high","low","close","volume","ct","qav","trades","tbav","tqav","ignore"])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    except:
        return None

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None:
        print(f"{symbol} verisi alınamadı.")
        return

    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df.dropna(subset=['close', 'volume'], inplace=True)

    if df.empty:
        print(f"{symbol} verisi boş.")
        return

    if df['volume'].isnull().any() or df['close'].isnull().any():
        print(f"{symbol} için hacim veya kapanış verisi NaN içeriyor.")
        return

    try:
        rsi = float(RSIIndicator(df['close'], window=14).rsi().iloc[-1])
    except Exception as e:
        print(f"{symbol} için RSI verisi hatalı: {e}")
        return

    try:
        macd_hist = float(MACD(df['close']).macd_diff().iloc[-1])
    except Exception as e:
        print(f"{symbol} için MACD verisi hatalı: {e}")
        return

    try:
        ema_fast = float(df['close'].ewm(span=9).mean().iloc[-1])
        ema_slow = float(df['close'].ewm(span=21).mean().iloc[-1])
        trend_up = ema_fast > ema_slow
        percent_diff = abs(ema_fast - ema_slow) / ema_slow * 100 if ema_slow > 0 else 0
    except Exception as e:
        print(f"{symbol} için EMA verisi hatalı: {e}")
        return
    
    # ATR hesaplama güvenli hâle getirildi
    try:
        high = float(df['high'].iloc[-1])
        low = float(df['low'].iloc[-1])
        close = float(df['close'].iloc[-1])
        atr_percent = (high - low) / close * 100
    except Exception as e:
        print(f"{symbol} için ATR verisi hatalı: {e}")
        return

    # Volume değişimi güvenli hâle getirildi
    try:
        last = df.iloc[-1].copy()
        prev = df.iloc[-2].copy()
        last_vol = float(str(last['volume']).replace(',', '').strip())
        prev_vol = float(str(prev['volume']).replace(',', '').strip())
        volume_change = ((last_vol - prev_vol) / prev_vol) * 100
    except Exception as e:
        print(f"{symbol} için hacim verisi hatalı: {e}")
        return

    # Trend hesaplama
    trend_up = ema_fast > ema_slow
    percent_diff = abs(ema_fast - ema_slow) / ema_slow * 100 if ema_slow > 0 else 0
    btc_trend = get_btc_trend()
    btc_dominance = get_btc_dominance()
    funding_rate = get_funding_rate(symbol)
    altbtc_strength = get_altbtc_strength(symbol)
    whale_spike = detect_whale_spike(df)
    oi = 12
    open_interest = oi
    ls_ratio = 1.2
    long_short_ratio = ls_ratio
    taker_ratio = 1.05
    usdt_dom = 5.4

    direction = "BUY" if rsi < 50 else "SELL"
    if direction is None:
        return

    # BUY yönünde ALTBTC zayıfsa sinyal bastır
    if direction == "BUY" and altbtc_strength == "ZAYIF":
        print(f"{symbol}: ALTBTC gücü zayıf olduğu için BUY sinyali bastırıldı.")
        return

    # Skor hesaplama
    score = (
        score_rsi(rsi, direction) +
        score_macd(macd_hist, direction) +
        score_volume_change(volume_change, direction) +
        score_trend(trend_up, direction) +
        score_btc_trend(btc_trend, direction) +
        score_btc_dominance(btc_dominance, direction) +
        score_altbtc_strength(altbtc_strength) +
        score_funding_rate(funding_rate) +
        score_whale_spike(whale_spike) +
        score_open_interest(open_interest) +
        score_long_short_ratio(long_short_ratio, direction) +
        score_taker_buy_sell(taker_ratio, direction) +
        score_usdt_dominance(usdt_dom) +
        score_ema_cross(ema_fast, ema_slow, direction) +
        score_atr(atr_percent)
    )

    total_score = score
    confidence = "GÜÇLÜ" if score >= 800 else "NORMAL" if score >= 400 else "ZAYIF"

    if confidence != "GÜÇLÜ":
        return

    try:
        ai_comment = generate_ai_comment(
            symbol, rsi, macd_hist, volume_change, trend_up, btc_trend,
            btc_dominance, funding_rate, whale_spike, open_interest,
            long_short_ratio, taker_ratio, usdt_dom, percent_diff, atr_percent,
            total_score, confidence
        )
    except Exception as e:
        ai_comment = f"AI yorumu alınamadı: {e}"

    sentiment, _ = get_market_sentiment_analysis(symbol, direction)
    message = f"""
    📊 {direction} Sinyali ({symbol})

    🔹 RSI: {round(rsi, 2)} → Skor: {score_rsi(rsi, direction)}
    🔹 MACD: {round(macd_hist, 4)} → Skor: {score_macd(macd_hist, direction)}
    🔹 Hacim Değişimi: %{round(volume_change, 2)} → Skor: {score_volume_change(volume_change, direction)}
    🔹 Trend: {'YUKARI' if trend_up else 'AŞAĞI'} → Skor: {score_trend(trend_up, direction)}
    🔹 BTC Trend: {btc_trend} → Skor: {score_btc_trend(btc_trend, direction)}
    🔹 BTC Dominance: %{round(btc_dominance, 2)} → Skor: {score_btc_dominance(btc_dominance, direction)}
    🔹 ALTBTC Gücü: {altbtc_strength} → Skor: {score_altbtc_strength(altbtc_strength)}
    🔹 Funding: %{round(funding_rate, 4)} → Skor: {score_funding_rate(funding_rate)}
    🔹 Whale Spike: {'VAR' if whale_spike else 'YOK'} → Skor: {score_whale_spike(whale_spike)}
    🔹 Open Interest: {round(open_interest, 2)}M → Skor: {score_open_interest(open_interest)}
    🔹 Long/Short Oranı: {long_short_ratio} → Skor: {score_long_short_ratio(long_short_ratio, direction)}
    🔹 Taker Buy/Sell: {taker_ratio} → Skor: {score_taker_buy_sell(taker_ratio, direction)}
    🔹 USDT Dominance: %{round(usdt_dom, 2)} → Skor: {score_usdt_dominance(usdt_dom)}
    🔹 EMA Cross: %{round(percent_diff, 2)} → Skor: {score_ema_cross(ema_fast, ema_slow, direction)}
    🔹 ATR: %{round(atr_percent, 2)} → Skor: {score_atr(atr_percent)}

    📈 Toplam Skor: {total_score} / 1500  
    📊 Ortalama Skor: {round(total_score / 15, 2)}  
    🔐 Güven Seviyesi: {confidence}
    """

    try:
        ai_comment = generate_ai_comment(
            symbol, rsi, macd_hist, volume_change, trend_up,
            btc_trend, btc_dominance, funding_rate, whale_spike,
            open_interest, long_short_ratio, taker_ratio,
            usdt_dom, percent_diff, atr_percent,
            total_score, confidence
        )

    except Exception as e:
        ai_comment = f"AI yorumu alınamadı: {e}"

    sentiment, _ = get_market_sentiment_analysis(symbol, direction)

    bot.send_message(
        chat_id=CHAT_ID,
        text=message + "\n\n🤖 Yapay Zeka Yorumu:\n" + ai_comment + "\n\n🧠 Sentiment:\n" + sentiment
    )

    symbols = [s['symbol'] for s in client.futures_exchange_info()['symbols'] if s['contractType']=='PERPETUAL' and s['quoteAsset']=='USDT']

while True:
    for sym in symbols:
        try:
            analyze_symbol(sym)
        except Exception as e:
            print(f"Hata: {sym} - {e}")
    time.sleep(60)