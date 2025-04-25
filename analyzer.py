import pandas as pd
from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def get_klines(symbol, interval="1h", limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"{symbol} verisi alınamadı: {e}")
        return None

def calculate_ema(data, period=20):
    return data['close'].ewm(span=period, adjust=False).mean()

def calculate_macd(data):
    exp1 = data['close'].ewm(span=12, adjust=False).mean()
    exp2 = data['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def generate_signal(symbol):
    df = get_klines(symbol)
    if df is None or len(df) < 50:
        return "Yetersiz veri", "Yetersiz veri", "Sinyal üretilmedi"

    ema20 = calculate_ema(df, 20)
    ema50 = calculate_ema(df, 50)
    macd, signal_line = calculate_macd(df)

    trend = "DÜŞÜŞ (EMA20 < EMA50)"
    if ema20.iloc[-1] > ema50.iloc[-1]:
        trend = "YÜKSELİŞ (EMA20 > EMA50)"

    momentum = "ZAYIF (MACD negatif)"
    if macd.iloc[-1] > signal_line.iloc[-1]:
        momentum = "GÜÇLÜ (MACD pozitif)"

    if trend.startswith("YÜKSELİŞ") and momentum.startswith("GÜÇLÜ"):
        final = "ALIM SİNYALİ"
    elif trend.startswith("DÜŞÜŞ") and momentum.startswith("ZAYIF"):
        final = "SATIM SİNYALİ"
    else:
        final = "NÖTR"

    return trend, momentum, final

def get_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"{symbol} fiyat alınamadı: {e}")
        return 0.0
