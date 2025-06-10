# btc_sniper_bot.py

import os
import time
import requests
import telegram
from dotenv import load_dotenv
from binance.client import Client

# Load .env variables
load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DRY_RUN = os.getenv("DRY_RUN", "True") == "True"

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

symbol = "BTCUSDT"
interval = "4H"


def get_klines():
    return client.get_klines(symbol=symbol, interval=interval, limit=50)


def find_support_resistance(prices):
    support = min(prices[-30:])
    resistance = max(prices[-30:])
    return support, resistance


def analyze():
    klines = get_klines()
    close_prices = [float(k[4]) for k in klines]
    volumes = [float(k[5]) for k in klines]

    rsi = calculate_rsi(close_prices)
    ema7 = calculate_ema(close_prices, 7)
    ema25 = calculate_ema(close_prices, 25)

    last_price = close_prices[-1]
    last_volume = volumes[-1]
    prev_avg_volume = sum(volumes[-6:-1]) / 5
    volume_spike = last_volume > prev_avg_volume * 1.3

    ema_cross_up = ema7[-2] < ema25[-2] and ema7[-1] > ema25[-1]
    ema_cross_down = ema7[-2] > ema25[-2] and ema7[-1] < ema25[-1]

    support, resistance = find_support_resistance(close_prices)
    is_near_support = last_price <= support * 1.02
    is_near_resistance = last_price >= resistance * 0.98

    score_long = int(rsi[-1] < 35) + int(ema_cross_up) + int(volume_spike) + int(is_near_support)
    score_short = int(rsi[-1] > 70) + int(ema_cross_down) + int(volume_spike) + int(is_near_resistance)

    if score_long >= 3:
        send_signal("LONG", last_price, rsi[-1], ema_cross_up, volume_spike, is_near_support, support, resistance, score_long)
    elif score_short >= 3:
        send_signal("SHORT", last_price, rsi[-1], ema_cross_down, volume_spike, is_near_resistance, support, resistance, score_short)


def calculate_rsi(prices, period=14):
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    seed = deltas[:period]
    up = sum(x for x in seed if x > 0) / period
    down = -sum(x for x in seed if x < 0) / period
    rs = up / down if down != 0 else 0
    rsi = [100 - 100 / (1 + rs)]
    for i in range(period, len(deltas)):
        delta = deltas[i]
        up_val = max(delta, 0)
        down_val = -min(delta, 0)
        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period
        rs = up / down if down != 0 else 0
        rsi.append(100 - 100 / (1 + rs))
    return rsi


def calculate_ema(prices, period):
    ema = [sum(prices[:period]) / period]
    k = 2 / (period + 1)
    for price in prices[period:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema


def send_signal(direction, price, rsi_val, ema_cross, volume_spike, zone_match, support, resistance, score):
    zone_text = "Destek" if direction == "LONG" else "Direnç"
    zone_status = "✅ Yakınında" if zone_match else "🚫 Uzakta"

    message = f"\n📌📌 BTC Sniper {direction} Sinyali\n\n" \
              f"🔹 Fiyat: {price}\n" \
              f"📊 RSI: {rsi_val:.2f} {'(dip)' if direction == 'LONG' else '(tepe)'}\n" \
              f"📊 EMA Kesişim: {'VAR' if ema_cross else 'YOK'}\n" \
              f"📊 Hacim Spike: {'VAR' if volume_spike else 'YOK'}\n" \
              f"📊 {zone_text} Bölgesi: {zone_status} ({'%.2f' % support if direction == 'LONG' else '%.2f' % resistance})\n" \
              f"💥 Güven Skoru: {score}/4\n\n" \
              f"⚙️ Emir: {'Simülasyon' if DRY_RUN else 'Gerçek'}\n"
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


if __name__ == "__main__":
    while True:
        try:
            analyze()
            time.sleep(900)  # 15 dakika
        except Exception as e:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ HATA: {str(e)}")
            time.sleep(60)
