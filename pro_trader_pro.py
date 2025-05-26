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

client = Client(API_KEY, API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

TIMEFRAME = "15m"
LIMIT = 150
RSI_LOW = 45
RSI_HIGH = 60

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

def get_btc_dominance():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global")
        data = response.json()
        return data["data"]["market_cap_percentage"]["btc"]
    except:
        return None
        
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

def get_funding_rate(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        response = requests.get(url)
        data = response.json()
        return float(data[0]["fundingRate"]) * 100
    except:
        return None

def detect_whale_volume_spike(df):
    try:
        volume_now = df['volume'].iloc[-1]
        volume_avg = df['volume'].iloc[-6:-1].mean()
        return volume_now > 2 * volume_avg
    except:
        return False

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
        
        def analyze_symbol(symbol):
    if symbol not in valid_symbols:
        return

    df = get_klines(symbol)
    if df is None or df.empty:
        return

    print(f"Analiz başlatıldı: {symbol}")

    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd_line = MACD(df['close']).macd().iloc[-1]
    macd_signal = MACD(df['close']).macd_signal().iloc[-1]
    macd_hist = MACD(df['close']).macd_diff().iloc[-1]

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if prev['volume'] == 0:
        return

    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100
    trend_up = df['close'].ewm(span=14).mean().iloc[-1] < df['close'].iloc[-1]
    trend_down = not trend_up
    btc_trend = get_btc_trend()

    buy_signal = rsi < RSI_LOW and macd_hist > 0.001 and macd_line > macd_signal and trend_up
    sell_signal = rsi > RSI_HIGH and macd_hist < -0.001 and macd_line < macd_signal and trend_down

    if buy_signal:
        direction = "BUY"
    elif sell_signal:
        direction = "SELL"
    else:
        return

    btc_dominance = get_btc_dominance()
    funding_rate = get_funding_rate(symbol)
    altbtc_strength = get_altbtc_strength(symbol) if not symbol.startswith("BTC") else "GÜÇLÜ"
    if altbtc_strength == "BİLİNMİYOR":
        altbtc_strength = "ZAYIF"
    if btc_dominance is None:
        btc_dominance = 50
    if funding_rate is None:
        funding_rate = 0
    whale_volume_spike = detect_whale_volume_spike(df)

    # PUANLAMA
    puan = 0
    if rsi < 40: puan += 1
    elif rsi > 65: puan -= 1
    if macd_hist > 0.005: puan += 1
    elif macd_hist < -0.005: puan -= 1
    if trend_up: puan += 1
    else: puan -= 1
    if volume_change > 30: puan += 1
    elif volume_change < 15: puan -= 1
    if whale_volume_spike: puan += 1
    if buy_signal and btc_trend == "UP": puan += 1
    if sell_signal and btc_trend == "DOWN": puan += 1
    if buy_signal and btc_trend == "DOWN": puan -= 2
    if sell_signal and btc_trend == "UP": puan -= 2
    if buy_signal and btc_dominance < 53: puan += 1
    if sell_signal and btc_dominance > 57: puan += 1
    if buy_signal and btc_dominance > 62: puan -= 1
    if sell_signal and btc_dominance < 50: puan -= 1
    if altbtc_strength == "GÜÇLÜ": puan += 1
    elif altbtc_strength == "ZAYIF": puan -= 1
    if abs(funding_rate) > 0.3: puan -= 1

    if puan >= 5:
        confidence = "GÜÇLÜ"
    elif puan >= 2:
        confidence = "NORMAL"
    else:
        confidence = "ZAYIF"

    if confidence == "ZAYIF":
        return

    message = (
        f"🚀KRİTİK AN!!! {direction} Sinyali: Hareket Zamanı\\n"
        f"Coin: {symbol}\\n"
        f"RSI: {round(rsi, 2)} | MACD: {round(macd_hist, 4)}\\n"
        f"Hacim Değişimi: %{round(volume_change, 2)}\\n"
        f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'} | BTC: {btc_trend}\\n"
        f"BTC Dominance: %{round(btc_dominance, 2)}\\n"
        f"ALTBTC Gücü: {altbtc_strength} | Funding: %{round(funding_rate, 4)}\\n"
        f"Whale + Hacim Spike: {'VAR' if whale_volume_spike else 'YOK'}\\n"
        f"Güven: {confidence}\\n"
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
        