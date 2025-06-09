import os
import time
import pandas as pd
import requests
import openai
import asyncio
from dotenv import load_dotenv
from binance.client import Client
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# Ortam değişkenleri
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

TIMEFRAME = "15m"
LIMIT = 150

def get_market_sentiment_analysis(symbol, direction):
    return "Sentiment verisi şu an kullanılamıyor.", None

def get_btc_trend():
    try:
        chg = float(client.get_ticker(symbol="BTCUSDT")["priceChangePercent"])
        return "UP" if chg >= 1.25 else "DOWN" if chg <= -1.25 else "SIDEWAYS"
    except: return "SIDEWAYS"

def get_btc_dominance():
    try:
        data = requests.get("https://api.coingecko.com/api/v3/global").json()
        return data["data"]["market_cap_percentage"]["btc"]
    except: return 50

def get_altbtc_strength(symbol):
    try:
        alt = symbol.replace("USDT", "") + "BTC"
        data = client.get_klines(symbol=alt, interval="15m", limit=5)
        closes = [float(k[4]) for k in data]
        return "GÜÇLÜ" if closes[-1] > closes[0] else "ZAYIF"
    except: return "ZAYIF"

def get_funding_rate(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        return float(requests.get(url).json()[0]["fundingRate"]) * 100
    except: return 0

def detect_whale_spike(df):
    try:
        now, avg = df['volume'].iloc[-1], df['volume'].iloc[-6:-1].mean()
        return now > 2 * avg
    except: return False

def get_klines(symbol):
    try:
        data = client.futures_klines(symbol=symbol, interval=TIMEFRAME, limit=LIMIT)
        df = pd.DataFrame(data, columns=["t","o","h","l","c","v","ct","qav","trades","tb","tq","ig"])
        df['close'] = pd.to_numeric(df['c'])
        df['volume'] = pd.to_numeric(df['v'])
        return df
    except: return None

def generate_ai_comment(symbol, rsi, rsi_prev, macd_now, macd_prev, volume_change, trend_up, btc_trend,
                         btc_dominance, funding_rate, whale, open_interest,
                         long_short, taker, usdt_dom, percent_diff, atr_percent,
                         altbtc):
    try:
        prompt = f"""
Sen deneyimli ve profesyonel bir kripto para teknik analiz uzmanısın.  
Aşağıdaki 15 teknik veriyi detaylı şekilde incele.  
Her göstergenin anlamını değerlendirerek mantıksal bir teknik analiz raporu hazırla.  
Son paragrafta ise tüm verilerin bütünlüğüne göre **net işlem önerisi sun**:  
👉 BUY / SELL / BEKLE.

Lütfen:
- Göstergelerin her biri hakkında kısa yorum yap (örneğin RSI düşük ama momentum yukarı, MACD pozitif ama zayıf vb.)
- Karar verirken göstergelerin teknik anlamına, yönüne ve birbirleriyle olan uyumuna odaklan.
- Ortalamaya veya gösterge sayısına göre değil, **uyumlu kombinasyonlara göre** karar ver.

📊 Teknik Veriler:
- Coin: {symbol}
- RSI: {rsi}
- RSI Momentum: {"YUKARI" if rsi > rsi_prev else "AŞAĞI"}
- MACD: {macd_now}
- MACD Momentum: {"YUKARI" if macd_now > macd_prev else "AŞAĞI"}
- Hacim Değişimi: %{round(volume_change, 2)}
- EMA Trend: {"YUKARI" if trend_up else "AŞAĞI"}
- EMA Gücü: %{round(percent_diff, 2)}
- BTC Trend: {btc_trend}
- BTC Dominance: %{round(btc_dominance, 2)}
- ALTBTC Gücü: {altbtc}
- Funding Rate: %{round(funding_rate, 4)}
- Whale Spike: {"VAR" if whale else "YOK"}
- Taker Buy/Sell: {taker}
- Long/Short: {long_short}
- USDT Dominance: %{usdt_dom}
- ATR: %{round(atr_percent, 2)}
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI yorumu alınamadı: {e}"

async def send_signal(msg):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None or df.empty: return

    try:
        rsi_series = RSIIndicator(df['close'], window=14).rsi()
        rsi_now = float(rsi_series.iloc[-1])
        rsi_prev = float(rsi_series.iloc[-2])
        macd_series = MACD(df['close']).macd_diff()
        macd_now = float(macd_series.iloc[-1])
        macd_prev = float(macd_series.iloc[-2])
        ema_fast = float(EMAIndicator(df['close'], window=12).ema_indicator().iloc[-1])
        ema_slow = float(EMAIndicator(df['close'], window=26).ema_indicator().iloc[-1])
        trend_up = ema_fast > ema_slow
        ema_diff_percent = abs(ema_fast - ema_slow) / ema_slow * 100 if ema_slow else 0
        high = float(df['h'].iloc[-1])
        low = float(df['l'].iloc[-1])
        close = float(df['close'].iloc[-1])
        atr_percent = (high - low) / close * 100
        last_vol = float(df['volume'].iloc[-1])
        prev_vol = float(df['volume'].iloc[-2])
        volume_change = ((last_vol - prev_vol) / prev_vol) * 100
    except: return

    direction = "BUY" if rsi_now < 50 else "SELL"

    # RSI momentum filtresi
    if (direction == "BUY" and rsi_now <= rsi_prev) or (direction == "SELL" and rsi_now >= rsi_prev):
        return

    # MACD momentum filtresi
    if (direction == "BUY" and macd_now <= macd_prev) or (direction == "SELL" and macd_now >= macd_prev):
        return

    # EMA kesişim gücü filtresi
    if ema_diff_percent < 0.2:
        return

    # Ön filtreleme – minimum 2 güçlü gösterge olması şartı
    buy_score = 0
    if (rsi_now < 35 and direction == "BUY") or (rsi_now > 70 and direction == "SELL"):
        buy_score += 1
    if (macd_now > 0.005 and direction == "BUY") or (macd_now < -0.005 and direction == "SELL"):
        buy_score += 1
    if (volume_change > 80 and direction == "BUY") or (volume_change < -50 and direction == "SELL"):
        buy_score += 1
    if (ema_fast > ema_slow * 1.002 and direction == "BUY") or (ema_fast < ema_slow * 0.998 and direction == "SELL"):
        buy_score += 1
    if buy_score < 3:
        print(f"[🧮 {symbol}] buy_score: {buy_score}")
        return


    btc_trend = get_btc_trend()
    btc_dominance = get_btc_dominance()
    funding_rate = get_funding_rate(symbol)
    altbtc = get_altbtc_strength(symbol)
    whale = detect_whale_spike(df)
    open_interest = 12
    long_short = 1.2
    taker = 1.05
    usdt_dom = 5.4

    try:
        ai_comment = generate_ai_comment(
            symbol, rsi_now, rsi_prev, macd_now, macd_prev, volume_change, trend_up, btc_trend,
            btc_dominance, funding_rate, whale, open_interest,
            long_short, taker, usdt_dom, ema_diff_percent, atr_percent, altbtc
        )
    except:
        ai_comment = "Yapay zeka yorum alınamadı."

    if "👉 BUY" in ai_comment or "👉 SELL" in ai_comment:  
        msg = f"""
    📊 AI Teknik Analiz ({symbol})

    {ai_comment}
    """
        print(f"Gönderilecek Mesaj:\n{msg}")
        asyncio.run(send_signal(msg))

symbols = [s['symbol'] for s in client.futures_exchange_info()['symbols'] 
           if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT']

while True:
    for sym in symbols:
        try:
            analyze_symbol(sym)
        except Exception as e:
            print(f"Hata: {sym} - {e}")
    time.sleep(60)
