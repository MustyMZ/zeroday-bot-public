import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD

load_dotenv()

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        print("Telegram gönderimi başarısız")
        
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

def get_klines(symbol, interval="15m", limit=150):
    try:
        data = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(data, columns=[
            'timestamp','open','high','low','close','volume','close_time',
            'qav','trades','tbbav','tbqav','ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        return df
    except:
        return None

def calculate_indicators(df):
    df['ema14'] = df['close'].ewm(span=14).mean()
    df['ema28'] = df['close'].ewm(span=28).mean()

    rsi = RSIIndicator(df['close'], window=14)
    df['rsi'] = rsi.rsi()

    macd = MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    df['atr'] = df['high'] - df['low']
    return df
    
    def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return

    if df['volume'].iloc[-2] == 0:
        return

    df = calculate_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    btc_trend = get_btc_trend()
    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100

    rsi = last['rsi']
    macd_hist = last['macd_hist']
    macd_signal = last['macd']
    macd_trigger = last['macd_signal']
    ema14 = last['ema14']
    ema28 = last['ema28']
    atr = last['atr']

    trend_up = ema14 > ema28
    trend_down = ema14 < ema28
    macd_buy = macd_hist > 0 and macd_signal > macd_trigger
    macd_sell = macd_hist < 0 and macd_signal < macd_trigger

    buy_signal = rsi < 40 and macd_buy and trend_up and btc_trend != "DOWN"
    sell_signal = rsi > 70 and macd_sell and trend_down and btc_trend != "UP"

    if buy_signal or sell_signal:
    direction = "BUY" if buy_signal else "SELL"
    confidence = "GÜÇLÜ" if volume_change > 40 else "NORMAL" if volume_change > 20 else "ZAYIF"
    message = (
        f"KRİTİK AN! {direction} Sinyali: Hareket Zamanı\n"
        f"Coin: {symbol}\n"
        f"RSI: {round(rsi,2)} | MACD: {round(macd_hist,5)}\n"
        f"Hacim Değişimi: {round(volume_change,2)}%\n"
        f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'} | BTC: {btc_trend}\n"
        f"Güven: {confidence}\n"
        f"(Dry-run mod: Gerçek emir gönderilmedi)"
    )
        send_telegram_message(message)
        
        def get_top_symbols(limit=200):
    info = client.futures_exchange_info()
    tickers = client.futures_ticker()
    valid_symbols = {
        s['symbol'] for s in info['symbols']
        if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT'
    }

    symbols_with_volume = [
        (t['symbol'], float(t['quoteVolume']))
        for t in tickers if t['symbol'] in valid_symbols
    ]
    sorted_symbols = sorted(symbols_with_volume, key=lambda x: x[1], reverse=True)
    return [s[0] for s in sorted_symbols[:limit]]

SYMBOLS = get_top_symbols()

while True:
    for symbol in SYMBOLS:
        try:
            analyze_symbol(symbol)
        except Exception as e:
            print(f"Hata: {symbol} - {e}")
    time.sleep(60)
    