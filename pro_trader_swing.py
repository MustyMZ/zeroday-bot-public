import ccxt
import time
import requests
import os
import pandas as pd

# ENV değişkenleri
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LIVE_MODE = os.getenv("LIVE_MODE", "False") == "True"

# Telegram gönderim fonksiyonu
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except:
        print("Telegram gönderimi başarısız")

# Geçerli coin listesi (binance futures'tan geçerli olanlar)
VALID_COINS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT",
    "DOGE/USDT", "XRP/USDT", "ADA/USDT", "DOT/USDT", "LINK/USDT",
    "ARB/USDT", "OP/USDT", "MATIC/USDT", "LTC/USDT", "ETC/USDT",
    "APE/USDT", "INJ/USDT", "PEPE/USDT", "1000SHIB/USDT", "TRX/USDT",
    "SEI/USDT", "SUI/USDT", "RNDR/USDT", "WIF/USDT", "TIA/USDT"
]

# Teknik analiz fonksiyonları
def calculate_indicators(df):
    df['ema14'] = df['close'].ewm(span=14, adjust=False).mean()
    df['ema28'] = df['close'].ewm(span=28, adjust=False).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    df['atr'] = df['high'] - df['low']
    return df

# Coin analiz fonksiyonu
def analyze_symbol(symbol, ohlcv):
    if not ohlcv or len(ohlcv) < 30:
        return

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = calculate_indicators(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if prev['volume'] == 0:
        return

    rsi = last['rsi']
    macd_hist = last['macd_hist']
    macd_signal = last['macd']
    macd_trigger = last['macd_signal']
    ema14 = last['ema14']
    ema28 = last['ema28']
    close_price = last['close']
    atr = last['atr']
    volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100

    trend_up = ema14 > ema28
    trend_down = ema14 < ema28
    macd_buy = macd_hist > 0 and macd_signal > macd_trigger
    macd_sell = macd_hist < 0 and macd_signal < macd_trigger

    buy_signal = rsi < 40 and macd_buy and trend_up
    sell_signal = rsi > 70 and macd_sell and trend_down

    if buy_signal:
        send_telegram_message(f"BUY Sinyali: {symbol} | RSI: {round(rsi,2)} | Hacim: %{round(volume_change,2)}")
    elif sell_signal:
        send_telegram_message(f"SELL Sinyali: {symbol} | RSI: {round(rsi,2)} | Hacim: %{round(volume_change,2)}")
        
        def main():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

    VALID_COINS = [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT", "DOGE/USDT", "ADA/USDT",
        "XRP/USDT", "LINK/USDT", "DOT/USDT", "MATIC/USDT", "LTC/USDT", "ATOM/USDT", "NEAR/USDT",
        "UNI/USDT", "APT/USDT", "ARB/USDT", "FIL/USDT", "INJ/USDT", "SUI/USDT", "OP/USDT", "AAVE/USDT",
        "RNDR/USDT", "TIA/USDT", "PEPE/USDT", "1000PEPE/USDT", "SEI/USDT", "W/USDT", "JOE/USDT",
        "THETA/USDT", "CFX/USDT", "BLUR/USDT", "CHZ/USDT", "GMT/USDT", "XLM/USDT", "DYDX/USDT",
        "ENJ/USDT", "SAND/USDT", "MANA/USDT", "EOS/USDT", "ALGO/USDT", "ZIL/USDT", "FLOW/USDT",
        "STORJ/USDT", "TRX/USDT", "XMR/USDT", "ETC/USDT", "RUNE/USDT", "GMX/USDT", "CAKE/USDT",
        "FXS/USDT", "GALA/USDT", "YGG/USDT", "AGIX/USDT", "T/USDT", "LINA/USDT", "DODO/USDT",
        "HOOK/USDT", "MAGIC/USDT", "ARPA/USDT", "LIT/USDT", "ILV/USDT", "LDO/USDT", "BEL/USDT",
        "STMX/USDT", "PHA/USDT", "BAND/USDT", "ALICE/USDT", "VET/USDT"
    ]

    while True:
        for symbol in VALID_COINS:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=30)
                analyze_symbol(symbol, ohlcv)
                time.sleep(1.2)
            except Exception as e:
                print(f"Hata: {symbol} - {str(e)}")
        time.sleep(60)

if __name__ == "__main__":
    main()