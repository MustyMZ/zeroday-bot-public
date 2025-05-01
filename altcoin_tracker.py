import requests
import time
import datetime
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

bot = Bot(token=TELEGRAM_BOT_TOKEN)
THRESHOLD_USDT = 200000

EXCLUDED_COINS = ['BTC', 'ETH', 'BNB', 'USDT', 'XRP', 'SOL', 'ADA', 'DOGE', 'TRX', 'DOT', 'MATIC', 'AVAX']

def fetch_all_pairs():
    url = "https://api.dexscreener.com/latest/dex/pairs"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("pairs", [])
        else:
            print("API hatası:", response.status_code)
    except Exception as e:
        print("API bağlantı hatası:", e)
    return []

def filter_large_altcoin_moves(pairs):
    results = []
    for pair in pairs:
        try:
            symbol = pair["baseToken"]["symbol"].upper()
            volume_raw = pair.get("volume", {}).get("h24")
            volume_usd = float(volume_raw) if volume_raw else 0.0
            price_raw = pair.get("priceUsd")
            price = float(price_raw) if price_raw else 0.0

            if symbol in EXCLUDED_COINS:
                continue
            if volume_usd >= THRESHOLD_USDT:
                results.append({
                    "symbol": symbol,
                    "volume": volume_usd,
                    "price": price,
                    "dex": pair.get("dexId", "Unknown DEX"),
                    "pair_url": pair.get("url", ""),
                })
        except Exception as e:
            print(f"{symbol} analiz hatası:", e)
            continue
    return results

def send_telegram_alert(coin_data):
    now = datetime.datetime.utcnow().strftime("%H:%M UTC - %d/%m/%Y")
    message = (
        f"ZERODAY Balina Tespiti:\n"
        f"Coin: ${coin_data['symbol']}\n"
        f"Transfer: {int(coin_data['volume']):,} USDT\n"
        f"Yön: Cüzdandan Borsaya (Satış Hazırlığı)\n"
        f"Tahmini Aksiyon: SHORT Sinyali\n"
        f"Zaman: {now}\n"
        f"Kaynak: {coin_data['pair_url']}"
    )
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def main():
    while True:
        print("Veriler taranıyor...")
        pairs = fetch_all_pairs()
        altcoin_moves = filter_large_altcoin_moves(pairs)
        for move in altcoin_moves:
            send_telegram_alert(move)
        print("Tüm coinler kontrol edildi. 60 sn bekleniyor...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()