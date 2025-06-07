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
🔔 AI Teknik Analiz – Coin: {symbol}

⚠️ FORMAT UYARISI:
Her teknik gösterge için şu yapıyı UYGULA (zorunlu):
→ GÖSTERGE: DEĞER → KATEGORİ → TEKNİK YORUM
Örn:
- RSI: 72.5 → YÜKSEK → Momentum YUKARI
- MACD: 0.0023 → YUKARI → Güçlü sinyal

Listeyi eksiksiz yazmadan devam etme.

📊 Teknik Göstergeler:

- RSI: {rsi} → {"YÜKSEK" if rsi > 70 else "DÜŞÜK" if rsi < 30 else "NÖTR"} → Momentum {"YUKARI" if rsi > rsi_prev else "AŞAĞI"}
- MACD: {macd_now:.5f} → {"YUKARI" if macd_now > macd_prev else "AŞAĞI"}
- Hacim: %{round(volume_change, 2)} → {"Artış" if volume_change > 0 else "Azalış"}
- EMA Trend: {"YUKARI" if trend_up else "AŞAĞI"} (%{round(percent_diff, 2)})
- BTC Trend: {btc_trend} → {"YUKARI" if btc_trend == "UP" else "AŞAĞI" if btc_trend == "DOWN" else "YATAY"}
- BTC Dominance: %{round(btc_dominance, 2)} → {"Pozitif" if btc_dominance < 50 else "Baskı"}
- ALTBTC Gücü: {altbtc}
- Funding Rate: %{round(funding_rate, 4)} → {"Long baskısı" if funding_rate > 0 else "Short baskısı"}
- Whale: {"VAR" if whale else "YOK"}
- Taker Buy/Sell: {taker}
- Long/Short: {long_short}
- USDT Dominance: %{usdt_dom}
- ATR: %{round(atr_percent, 2)} → {"Yüksek volatilite" if atr_percent > 1.5 else "Normal"}

🧠 AI Yorumu (1 paragraf yaz):
Genel teknik görünümü değerlendir, aşırı detay verme.  

📌 İşlem Önerisi (tek satır): BUY / SELL / BEKLE  
Kaldıraç: 15x  
TP/SL: RSI veya EMA'ya göre ayarlanmalı.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except:
        return "Yapay zeka yorumu oluşturulamadı."

async def send_signal(msg):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def analyze_symbol(symbol):
    df = get_klines(symbol)
    
    if df is None or df.empty:
        print(f"[⛔️ KLINE HATASI] {symbol} → Veri alınamadı ya da boş geldi.")
        return
    else:
        print(f"[✅ KLINE OK] {symbol} → Veri alındı.")
        print(df.tail(1))  # son kapanış mumu
    

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
        print(f"[🔍 {symbol}] RSI: {rsi_now:.2f}, MACD: {macd_now:.4f}, Volume Change: %{volume_change:.2f}, EMA Diff: %{ema_diff_percent:.2f}")
    except: return

    direction = "BUY" if rsi_now < 50 else "SELL"

    # RSI momentum filtresi
    if (direction == "BUY" and rsi_now <= rsi_prev) or (direction == "SELL" and rsi_now >= rsi_prev):
        return

    # MACD momentum filtresi
    if (direction == "BUY" and macd_now <= macd_prev) or (direction == "SELL" and macd_now >= macd_prev):
        return

    # EMA kesişim gücü filtresi
    if ema_diff_percent < 0.7:
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
    if buy_score < 2:
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
        print(f"[🤖 GPT ANALİZ] {symbol} → AI analiz gönderiliyor...")
        ai_comment = generate_ai_comment(
            symbol, rsi_now, rsi_prev, macd_now, macd_prev, volume_change, trend_up, btc_trend,
            btc_dominance, funding_rate, whale, open_interest,
            long_short, taker, usdt_dom, ema_diff_percent, atr_percent, altbtc
        )
    except Exception as e:
        print(f"AI Yorum Hatası: {e}")
        ai_comment = "Yapay zeka yorum alınamadı."
        

    if True:
        # AI yorumundan işlem yönünü çek
        action = "BEKLE"
        for line in ai_comment.splitlines():
            if "İşlem Önerisi" in line:
                if "BUY" in line: action = "BUY"
                elif "SELL" in line: action = "SELL"
                break

        # Başlıkta coin + işlem yönü olacak şekilde mesajı hazırla
        msg = f"""
    🔔 📊 AI Teknik Analiz ({symbol}) – İşlem: {action}

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
