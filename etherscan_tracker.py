import requests
import time
import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from telegram import Bot

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# TEST için tek adres (örnek holder)
TEST_ADDRESSES = {
    "PEPE": {
        "contract": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "price_usd": 0.0000012,
        "wallet": "0x000000000000000000000000000000000000dead"
    }
}

ETHPLORER_API = "https://api.ethplorer.io"
ETHPLORER_KEY = "freekey"

def get_wallet_history(address):
    url = f"{ETHPLORER_API}/getAddressHistory/{address}?apiKey={ETHPLORER_KEY}&type=transfer&limit=10"
    try:
        res = requests.get(url)
        data = res.json()
        return data.get("operations", [])
    except Exception as e:
        print(f"History alınamadı: {e}")
        return []

def send_telegram(coin, address, usd_value, token_amount, tx_hash):
    now = datetime.datetime.utcnow().strftime("%H:%M UTC - %d/%m/%Y")
    msg = (
        f"ZERODAY Balina Tespiti (TEST):\n"
        f"Coin: ${coin}\n"
        f"Cüzdan: {address}\n"
        f"Alım: {token_amount:,.0f} adet (~{usd_value:,.0f} USD)\n"
        f"Zaman: {now}\n"
        f"İşlem: https://etherscan.io/tx/{tx_hash}"
    )
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def check_receive():
    for coin, data in TEST_ADDRESSES.items():
        address = data["wallet"]
        price = data["price_usd"]
        history = get_wallet_history(address)
        for tx in history:
            if tx["tokenInfo"]["address"].lower() != data["contract"].lower():
                continue
            if tx["type"] != "receive":
                continue
            token_amount = float(tx["value"])
            usd_value = token_amount * price
            if usd_value >= 500_000:
                send_telegram(coin, address, usd_value, token_amount, tx["transactionHash"])

def main():
    print("ZERODAY test takibi başladı...")
    while True:
        check_receive()
        print("Kontrol tamamlandı. 60 sn bekleniyor...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()