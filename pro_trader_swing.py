import os
import ccxt
import pandas as pd
import numpy as np
import ta
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LIVE_MODE = os.getenv("LIVE_MODE", "False") == "True"

exchange = ccxt.binance()
markets = exchange.load_markets()

VALID_COINS = [
    "1INCH/USDT", "AAVE/USDT", "ADA/USDT", "AGIX/USDT", "ALGO/USDT", "ALICE/USDT", "ANKR/USDT", "APE/USDT", "APT/USDT",
    "AR/USDT", "ARB/USDT", "ATOM/USDT", "AVAX/USDT", "AXS/USDT", "BAND/USDT", "BCH/USDT", "BLUR/USDT", "BNB/USDT",
    "BTC/USDT", "C98/USDT", "CELO/USDT", "CELR/USDT", "CHZ/USDT", "CKB/USDT", "COMP/USDT", "COTI/USDT", "CRV/USDT",
    "CTSI/USDT", "DASH/USDT", "DENT/USDT", "DGB/USDT", "DOGE/USDT", "DOT/USDT", "DYDX/USDT", "EGLD/USDT", "ENJ/USDT",
    "ENS/USDT", "EOS/USDT", "ETC/USDT", "ETH/USDT", "FET/USDT", "FIL/USDT", "FLM/USDT", "FLOW/USDT", "FTM/USDT",
    "FXS/USDT", "GALA/USDT", "GAL/USDT", "GMT/USDT", "GMX/USDT", "GRT/USDT", "HBAR/USDT", "HFT/USDT", "ICP/USDT",
    "ICX/USDT", "ID/USDT", "IMX/USDT", "INJ/USDT", "IOST/USDT", "IOTA/USDT", "JASMY/USDT", "JOE/USDT", "JTO/USDT",
    "KAVA/USDT", "KLAY/USDT", "KNC/USDT", "LDO/USDT", "LINA/USDT", "LINK/USDT", "LIT/USDT", "LPT/USDT", "LTC/USDT",
    "MAGIC/USDT", "MANA/USDT", "MASK/USDT", "MATIC/USDT", "MINA/USDT", "MKR/USDT", "MTL/USDT", "NEAR/USDT",
    "NKN/USDT", "OCEAN/USDT", "OGN/USDT", "OMG/USDT", "ONE/USDT", "ONT/USDT", "OP/USDT", "ORDI/USDT", "OXT/USDT",
    "PEOPLE/USDT", "PERP/USDT", "PHA/USDT", "QNT/USDT", "REEF/USDT", "REN/USDT", "RNDR/USDT", "ROSE/USDT",
    "RUNE/USDT", "RVN/USDT", "SAND/USDT", "SFP/USDT", "SKL/USDT", "SNX/USDT", "SOL/USDT", "SPELL/USDT", "SSV/USDT",
    "STG/USDT", "STMX/USDT", "STORJ/USDT", "STPT/USDT", "STX/USDT", "SUI/USDT", "SUSHI/USDT", "SXP/USDT",
    "THETA/USDT", "TOMO/USDT", "TRB/USDT", "TWT/USDT", "UMA/USDT", "UNFI/USDT", "UNI/USDT", "VET/USDT",
    "WAVES/USDT", "WOO/USDT", "XEM/USDT", "XLM/USDT", "XMR/USDT", "XRP/USDT", "XTZ/USDT", "XVS/USDT", "YFI/USDT",
    "ZEC/USDT", "ZEN/USDT", "ZIL/USDT", "ZRX/USDT"
]

MAX_OPEN_TRADES = 3
MAX_POSITION_SIZE = 100

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def get_ohlcv(symbol, timeframe='15m', limit=50):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception as e:
        print(f"HATA OHLCV: {symbol} {e}")
        return []

def calculate_indicators(df):
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    df['ema14'] = ta.trend.EMAIndicator(close, window=14).ema_indicator()
    df['ema28'] = ta.trend.EMAIndicator(close, window=28).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()
    return df
    
    def analyze(symbol):
    ohlcv = get_ohlcv(symbol)
    if not ohlcv or len(ohlcv) < 30:
        return

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = calculate_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    rsi = last['rsi']
    macd_hist = last['macd_hist']
    macd_signal = last['macd']
    macd_trigger = last['macd_signal']
    ema14 = last['ema14']
    ema28 = last['ema28']
    close_price = last['close']
    atr = last['atr']

    if prev['volume'] == 0:
    volume_change = 0
    else:
    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100

    trend_up = ema14 > ema28
    trend_down = ema14 < ema28
    macd_buy = macd_hist > 0 and macd_signal > macd_trigger
    macd_sell = macd_hist < 0 and macd_signal < macd_trigger

    buy_signal = rsi < 40 and macd_buy and trend_up and volume_change > 40
    sell_signal = rsi > 70 and macd_sell and trend_down and volume_change > 40

    tp_percent = 6 if buy_signal else 4
    sl_percent = 2

    signal_strength = "GÜÇLÜ" if volume_change > 50 and ((buy_signal and rsi < 30) or (sell_signal and rsi > 75)) else "NORMAL"
    action = "BUY" if buy_signal else "SELL" if sell_signal else None

    if action:
        tp_price = close_price * (1 + tp_percent / 100) if action == "BUY" else close_price * (1 - tp_percent / 100)
        sl_price = close_price * (1 - sl_percent / 100) if action == "BUY" else close_price * (1 + sl_percent / 100)

        msg = f"[SİNYAL: {signal_strength} {action}]\\n"
        msg += f"Coin: {symbol}\\n"
        msg += f"Fiyat: {close_price:.4f}\\n"
        msg += f"RSI: {rsi:.2f} | MACD: {'YUKARI' if macd_buy else 'AŞAĞI'}\\n"
        msg += f"Hacim Değişimi: %{volume_change:.2f}\\n"
        msg += f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'}\\n"
        msg += f"TP: %{tp_percent:.1f} ({tp_price:.4f}) | SL: %{sl_percent:.1f} ({sl_price:.4f})\\n"
        msg += f"Durum: {'GERÇEK EMİR' if LIVE_MODE else 'TEST MODU'}"

        send_telegram(msg)

while True:
    usdt_markets = VALID_COINS
    for symbol in usdt_markets:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)