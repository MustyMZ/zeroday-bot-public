import os
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import pearsonr
from ta.momentum import RSIIndicator
from dotenv import load_dotenv
import telegram

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

BINANCE_URL = "https://api.binance.com"
HEADERS = {"User-Agent": "DecoupledDetector/1.0"}

def get_binance_futures_symbols():
    url = f"{BINANCE_URL}/fapi/v1/exchangeInfo"
    data = requests.get(url).json()
    symbols = [
        s["symbol"] for s in data["symbols"]
        if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"
    ]
    return sorted(list(set(symbols)))

def get_klines(symbol, interval='1h', limit=24):
    url = f"{BINANCE_URL}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def get_close_prices(symbol, interval='1h', limit=24):
    klines = get_klines(symbol, interval, limit)
    return [float(k[4]) for k in klines]

def get_volume_change(symbol):
    klines = get_klines(symbol, '1h', 2)
    if len(klines) < 2:
        return 0
    vol_now = float(klines[-1][5])
    vol_prev = float(klines[-2][5])
    return ((vol_now - vol_prev) / vol_prev) * 100 if vol_prev > 0 else 0

def get_btc_dominance():
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["market_cap_percentage"]["btc"]
    return 0

def calculate_rsi(prices, period=14):
    try:
        rsi = RSIIndicator(pd.Series(prices), window=period).rsi()
        return round(rsi.iloc[-1], 2)
    except:
        return 0

def get_altbtc_strength(coin_symbol):
    base = coin_symbol.replace("USDT", "")
    altbtc_symbol = f"{base}BTC"
    url = f"{BINANCE_URL}/api/v3/klines?symbol={altbtc_symbol}&interval=1h&limit=2"
    res = requests.get(url)
    if res.status_code != 200:
        return False
    klines = res.json()
    try:
        close_now = float(klines[-1][4])
        close_prev = float(klines[-2][4])
        return close_now > close_prev
    except:
        return False
        
        def get_btc_prices():
    return get_close_prices("BTCUSDT")

def get_decoupled_coins():
    btc_prices = get_btc_prices()
    if not btc_prices:
        return []

    btc_dominance = get_btc_dominance()
    symbols = get_binance_futures_symbols()
    results = []

    for symbol in symbols:
        if "DOWN" in symbol or "UP" in symbol or "BULL" in symbol or "BEAR" in symbol:
            continue

        prices = get_close_prices(symbol)
        if len(prices) < 20:
            continue

        try:
            rsi = calculate_rsi(prices)
            volume_change = get_volume_change(symbol)
            corr, _ = pearsonr(btc_prices, prices)
        except:
            continue

        # Filtreler
        filters = {
            "korelasyon": abs(corr) < 0.3,
            "rsi": rsi > 50,
            "volume": volume_change > 30,
            "dominance": btc_dominance > 50 and prices[-1] > prices[-2],
            "altbtc": get_altbtc_strength(symbol),
            "whale": volume_change > 50,
            "candlestick": prices[-1] > prices[-2] and prices[-2] < prices[-3],
            "atr_spike": abs(prices[-1] - prices[-2]) > (np.std(prices[-14:])),
            "social_hype": "FLOKI" in symbol or "PEPE" in symbol  # örnek
        }

        score = sum(filters.values())

        if score >= 6:
            results.append({
                "symbol": symbol,
                "score": score,
                "corr": round(corr, 2),
                "rsi": rsi,
                "volume": round(volume_change, 2),
                "dominance": btc_dominance,
                "filters": filters
            })

    return results

def send_telegram_alert(signal):
    symbol = signal["symbol"]
    text = f"""🚀 *AYRIŞMA TESPİTİ: {symbol}*

Korelasyon (BTC): `{signal['corr']}`
RSI: `{signal['rsi']}` | Hacim Artışı: `{signal['volume']}%`
BTC Dominance: `{signal['dominance']}%`
ALTBTC Gücü: `{"VAR" if signal['filters']['altbtc'] else "YOK"}`
Whale / Volatilite: `{"VAR" if signal['filters']['whale'] else "ZAYIF"}`
Mum Formasyonu: `{"Pozitif" if signal['filters']['candlestick'] else "Yok"}`
Sosyal Hype: `{"Trend olabilir" if signal['filters']['social_hype'] else "Yok"}`

*Karar:* {generate_comment(signal['score'])}
"""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode="Markdown")

def generate_comment(score):
    if score >= 8:
        return "GÜÇLÜ ayrışma. İzlemeye değer. Smart para etkisi olabilir."
    elif score >= 6:
        return "Normal seviyede ayrışma. Takibe alınabilir."
    else:
        return "Zayıf sinyal. İşlem önerilmez."
        
        def main():
    print("📡 Ayrışan Coin Tarayıcı Başladı...")
    while True:
        try:
            decoupled = get_decoupled_coins()
            if decoupled:
                for signal in decoupled:
                    send_telegram_alert(signal)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Uygun ayrışma sinyali bulunamadı.")
        except Exception as e:
            print("HATA:", e)
        time.sleep(3600)  # 1 saatte bir tarar

if __name__ == "__main__":
    main()