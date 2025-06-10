# btc_sniper_alarm.py
import time
import requests
import datetime

# === AYARLAR ===
TELEGRAM_BOT_TOKEN = '7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE'
TELEGRAM_CHAT_ID = '6150871845'
CHECK_INTERVAL = 15  # saniye
PRICE_CHANGE_THRESHOLD = 0.005  # %0.5 değişim

# === DURUM TAKİBİ ===
last_price = None
last_volume = None

def get_btc_price_volume():
    url = 'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT'
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data['lastPrice']), float(data['quoteVolume'])
    except:
        return None, None

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=payload)
    except:
        pass

def format_time():
    now = datetime.datetime.now().strftime('%H:%M:%S')
    return f"[{now}]"

# === ANA DÖNGÜ ===
print("Sniper alarm başlatıldı...")

while True:
    price, volume = get_btc_price_volume()
    
    if price is None:
        print("Veri alınamadı. Tekrar deneniyor...")
        time.sleep(CHECK_INTERVAL)
        continue

    if last_price is not None:
        change = (price - last_price) / last_price

        if change >= PRICE_CHANGE_THRESHOLD:
            msg = (
                f"{format_time()} BTC son 15 saniyede %{change*100:.2f} yükseldi.\n"
                f"DENT, TRB, LQTY grafiklerine HEMEN bak! 🚨"
            )
            send_telegram_message(msg)
            print(msg)

    last_price = price
    last_volume = volume
    time.sleep(CHECK_INTERVAL)