import ccxt
import time
import requests
import pandas as pd
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LIVE_MODE = os.getenv("LIVE_MODE", "False") == "True"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except:
        print("Telegram gönderimi başarısız")

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

markets = exchange.load_markets()
usdt_markets = [s for s in markets if "/USDT" in s and markets[s]['active'] and markets[s]['type'] == 'future']
top_200 = usdt_markets[:200]

def calculate_indicators(df):
    df['ema14'] = df['close'].ewm(span=14).mean()
    df['ema28'] = df['close'].ewm(span=28).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    df['atr'] = df['high'] - df['low']
    return df

def analyze_symbol(symbol, ohlcv):
    if not ohlcv or len(ohlcv) < 30:
        return

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = calculate_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if (
        prev['volume'] is None 
        or last['volume'] is None 
        or prev['volume'] == 0 
        or pd.isna(prev['volume']) 
        or pd.isna(last['volume'])
    ):
        volume_change = 0
    else:
        volume_change = ((last['volume'] - prev['volume']) / prev['volume']) * 100

    rsi = last['rsi']
    macd_hist = last['macd_hist']
    macd_signal = last['macd']
    macd_trigger = last['macd_signal']
    ema14 = last['ema14']
    ema28 = last['ema28']

    trend_up = ema14 > ema28
    trend_down = ema14 < ema28
    macd_buy = macd_hist > 0 and macd_signal > macd_trigger
    macd_sell = macd_hist < 0 and macd_signal < macd_trigger

    buy_signal = rsi < 50 and macd_buy and trend_up
    sell_signal = rsi > 50 and macd_sell and trend_down

    if buy_signal or sell_signal:
        signal_type = "BUY" if buy_signal else "SELL"
        print(f"{signal_type} sinyali oluştu: {symbol}")
        confidence = "GÜÇLÜ" if volume_change > 40 else "NORMAL" if volume_change > 20 else "ZAYIF"
        direction = "📈 YÜKSELİŞ POTANSİYELİ:" if signal_type == "BUY" else "📉 DÜŞÜŞ SİNYALİ:"
        header = f"[YUMUSAK SİNYAL] {direction} {symbol}"

        message = (
            f"{header}\n"
            f"RSI: {round(rsi,2)} | MACD: {round(macd_hist,5)}\n"
            f"Hacim Değişimi: {round(volume_change,2)}%\n"
            f"Trend: {'YUKARI' if trend_up else 'AŞAĞI'}\n"
            f"Güven: {confidence}\n"
            f"(Dry-run mod: Gerçek emir gönderilmedi)"
        )
        send_telegram_message(message)

def main():
    print(f"Sembol sayısı: {len(top_200)}")
    while True:
        for symbol in top_200:
            try:
                print(f"Veri alınıyor: {symbol}")
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=30)
                analyze_symbol(symbol, ohlcv)
                time.sleep(1.2)
            except Exception as e:
                print(f"Hata: {symbol} – {str(e)}")
        time.sleep(60)

if __name__ == "__main__":
    main()