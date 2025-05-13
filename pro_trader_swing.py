import os
import time
import ccxt
import requests
import pandas as pd
import ta

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LIVE_MODE = os.getenv("LIVE_MODE", "False") == "True"

VALID_COINS = [
    "1INCH/USDT", "AAVE/USDT", "ADA/USDT", "AGIX/USDT", "ALGO/USDT", "APE/USDT", "APT/USDT", "AR/USDT",
    "ARB/USDT", "ATOM/USDT", "AVAX/USDT", "AXS/USDT", "BAND/USDT", "BCH/USDT", "BNB/USDT", "BTC/USDT",
    "CELO/USDT", "CHZ/USDT", "COMP/USDT", "CRV/USDT", "DASH/USDT", "DOGE/USDT", "DOT/USDT", "DYDX/USDT",
    "EGLD/USDT", "ENJ/USDT", "ENS/USDT", "EOS/USDT", "ETC/USDT", "ETH/USDT", "FET/USDT", "FIL/USDT",
    "FLOW/USDT", "FTM/USDT", "GALA/USDT", "GAL/USDT", "GMT/USDT", "GMX/USDT", "GRT/USDT", "HBAR/USDT",
    "ICP/USDT", "IMX/USDT", "INJ/USDT", "JASMY/USDT", "KAVA/USDT", "KLAY/USDT", "LDO/USDT", "LINK/USDT",
    "LTC/USDT", "MANA/USDT", "MASK/USDT", "MATIC/USDT", "MINA/USDT", "NEAR/USDT", "OP/USDT", "ORDI/USDT",
    "RNDR/USDT", "ROSE/USDT", "RUNE/USDT", "SAND/USDT", "SOL/USDT", "STMX/USDT", "STORJ/USDT", "STPT/USDT",
    "STX/USDT", "SUI/USDT", "SUSHI/USDT", "TRB/USDT", "UNI/USDT"
]

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    df['ema14'] = ta.trend.EMAIndicator(close=df['close'], window=14).ema_indicator()
    df['ema28'] = ta.trend.EMAIndicator(close=df['close'], window=28).ema_indicator()
    df['atr'] = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
    return df

def analyze_symbol(symbol, ohlcv):
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

    buy_signal = rsi < 40 and macd_buy and trend_up
    sell_signal = rsi > 70 and macd_sell and trend_down
    
        if buy_signal or sell_signal:
        signal_type = "BUY" if buy_signal else "SELL"
        confidence = "GÜÇLÜ" if volume_change > 40 else "NORMAL" if volume_change > 20 else "ZAYIF"
        tp_percent = 6 if buy_signal else 4
        sl_percent = 2

        message = (
            f"{signal_type} Sinyali: {symbol}\n"
            f"RSI: {round(rsi,2)} | MACD: {round(macd_hist,5)}\n"
            f"Hacim Değişimi: {round(volume_change,2)}%\n"
            f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'}\n"
            f"Güven: {confidence}\n"
            f"Kaldıraç: 10x | TP: %{tp_percent} | SL: %{sl_percent}\n"
            f"(Test modu: Emir gönderilmedi)"
        )

        send_telegram(message)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except:
        print("Telegram gönderimi başarısız")

def main():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

    while True:
        for symbol in VALID_COINS:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=30)
                analyze_symbol(symbol, ohlcv)
                time.sleep(1.2)  # API koruması
            except Exception as e:
                print(f"Hata: {symbol} - {str(e)}")
        time.sleep(60)

if __name__ == "__main__":
    main()