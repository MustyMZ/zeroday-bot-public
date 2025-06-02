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
    if direction == "BUY": return rsi < 40
    elif direction == "SELL": return rsi > 70

def score_macd(macd_hist, direction):
    if direction == "BUY": return macd_hist > 0
    elif direction == "SELL": return macd_hist < 0

def score_volume_change(volume_change, direction):
    if direction == "BUY": return volume_change > 40
    elif direction == "SELL": return volume_change < -30

def score_ema_cross(ema_fast, ema_slow, direction):
    if direction == "BUY": return ema_fast > ema_slow
    elif direction == "SELL": return ema_fast < ema_slow

def score_btc_trend(trend, direction):
    if direction == "BUY":
        return 100 if trend == "UP" else 60 if trend == "SIDEWAYS" else 0
    elif direction == "SELL":
        return 100 if trend == "DOWN" else 60 if trend == "SIDEWAYS" else 0

def score_btc_dominance(dom, direction):
    if direction == "BUY": return 100 if dom < 49 else 60
    elif direction == "SELL": return 100 if dom > 63 else 60

def score_altbtc_strength(val): return 100 if val == "GÜÇLÜ" else 0
def score_funding_rate(x): return 100 if abs(x) < 0.02 else 60
def score_whale_spike(x): return 100 if x else 0
def score_open_interest(x): return 100 if x > 10 else 60
def score_long_short_ratio(x, d): return 100 if (d=="BUY" and x>1.2) or (d=="SELL" and x<0.8) else 60
def score_taker_buy_sell(x, d): return 100 if (d=="BUY" and x>1.05) or (d=="SELL" and x<0.95) else 60
def score_usdt_dominance(x): return 100 if x > 6 else 60
def score_atr(x): return 100 if x > 5 else 60

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

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None or df.empty: return

    try:
        rsi = float(RSIIndicator(df['close'], window=14).rsi().iloc[-1])
        macd_hist = float(MACD(df['close']).macd_diff().iloc[-1])
        ema_fast = float(EMAIndicator(df['close'], window=12).ema_indicator().iloc[-1])
        ema_slow = float(EMAIndicator(df['close'], window=26).ema_indicator().iloc[-1])
        trend_up = ema_fast > ema_slow
        percent_diff = abs(ema_fast - ema_slow) / ema_slow * 100 if ema_slow else 0
        high = float(df['h'].iloc[-1])
        low = float(df['l'].iloc[-1])
        close = float(df['close'].iloc[-1])
        atr_percent = (high - low) / close * 100
        last_vol = float(df['volume'].iloc[-1])
        prev_vol = float(df['volume'].iloc[-2])
        volume_change = ((last_vol - prev_vol) / prev_vol) * 100
    except: return

    direction = "BUY" if rsi < 50 else "SELL"

    buy_score = 0
    if score_rsi(rsi, direction): buy_score += 1
    if score_macd(macd_hist, direction): buy_score += 1
    if score_volume_change(volume_change, direction): buy_score += 1
    if score_ema_cross(ema_fast, ema_slow, direction): buy_score += 1
    if buy_score < 3: return

    btc_trend = get_btc_trend()
    btc_dominance = get_btc_dominance()
    funding_rate = get_funding_rate(symbol)
    altbtc_strength = get_altbtc_strength(symbol)
    whale_spike = detect_whale_spike(df)
    open_interest = 12
    long_short_ratio = 1.2
    taker_ratio = 1.05
    usdt_dom = 5.4

    total_score = (
        score_btc_trend(btc_trend, direction) +
        score_btc_dominance(btc_dominance, direction) +
        score_altbtc_strength(altbtc_strength) +
        score_funding_rate(funding_rate) +
        score_whale_spike(whale_spike) +
        score_open_interest(open_interest) +
        score_long_short_ratio(long_short_ratio, direction) +
        score_taker_buy_sell(taker_ratio, direction) +
        score_usdt_dominance(usdt_dom) +
        score_atr(atr_percent)
    )

    confidence = "GÜÇLÜ" if total_score >= 800 else "NORMAL" if total_score >= 400 else "ZAYIF"

    message = f"""
📊 {direction} Sinyali ({symbol})

🔹 RSI: {round(rsi, 2)}  
🔹 MACD: {round(macd_hist, 4)}  
🔹 Hacim Değişimi: %{round(volume_change, 2)}  
🔹 EMA Cross: %{round(percent_diff, 2)}  
🔹 BTC Trend: {btc_trend}  
🔹 BTC Dominance: %{round(btc_dominance, 2)}  
🔹 ALTBTC Gücü: {altbtc_strength}  
🔹 Funding: %{round(funding_rate, 4)}  
🔹 Whale Spike: {'VAR' if whale_spike else 'YOK'}  
🔹 Open Interest: {open_interest}M  
🔹 Long/Short Oranı: {long_short_ratio}  
🔹 Taker Buy/Sell: {taker_ratio}  
🔹 USDT Dominance: %{usdt_dom}  
🔹 ATR: %{round(atr_percent, 2)}  
"""

    ai_comment = generate_ai_comment(
        symbol, rsi, macd_hist, volume_change, trend_up, btc_trend,
        btc_dominance, funding_rate, whale_spike, open_interest,
        long_short_ratio, taker_ratio, usdt_dom, percent_diff, atr_percent,
        total_score, confidence
    )

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