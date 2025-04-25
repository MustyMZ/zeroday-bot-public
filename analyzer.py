# analyzer.py
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import numpy as np

API_KEY = 'BINANCE_API_KEY'
API_SECRET = 'BINANCE_SECRET_KEY'

client = Client(API_KEY, API_SECRET)

def get_klines(symbol="BTCUSDT", interval="1h", limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except BinanceAPIException as e:
        print(f"Binance API error: {e}")
        return None

def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()

def calculate_macd(data):
    ema12 = data['close'].ewm(span=12, adjust=False).mean()
    ema26 = data['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def generate_signal(symbol="BTCUSDT"):
    df = get_klines(symbol)
    if df is None or df.empty:
        return f"{symbol} - Veriler alınamadı."

    df['RSI'] = calculate_rsi(df)
    df['EMA20'] = calculate_ema(df, 20)
    df['EMA50'] = calculate_ema(df, 50)
    df['MACD'], df['Signal'] = calculate_macd(df)

    latest = df.iloc[-1]

    signals = []

    if latest['RSI'] < 30:
        signals.append("RSI Aşırı Satım (Alım sinyali)")
    elif latest['RSI'] > 70:
        signals.append("RSI Aşırı Alım (Satım sinyali)")

    if latest['EMA20'] > latest['EMA50']:
        signals.append("EMA20 > EMA50 (Yükseliş trendi)")
    else:
        signals.append("EMA20 < EMA50 (Düşüş trendi)")

    if latest['MACD'] > latest['Signal']:
        signals.append("MACD kesişimi POZİTİF")
    else:
        signals.append("MACD kesişimi NEGATİF")

    return f"{symbol} Teknik Analiz:\n" + "\n".join(signals)
