import requests
import time
import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from telegram import Bot

bot = Bot(token=TELEGRAM_BOT_TOKEN)

COINS = {
    "PEPE": {
        "contract": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "price_usd": 0.0000012
    },
    "FLOKI": {
        "contract": "0xfb5b838b6cfeedc2873ab27866079ac55363d37e",
        "price_usd": 0.00018
    },
    "BONK": {
        "contract": "0x5c74eb2f812c0674f2edcb204b1c5b7cdca1e9f0",
        "price_usd": 0.000028
    },
    "PONKE": {
        "contract": "0xf8A0637b42843f9E8cfd4FDb68C49Cbf2f730A00",
        "price_usd": 0.0025
    }
}

ETHPLORER_API = "https://api.ethplorer.io"
ETHPLORER_KEY = "freekey"

def get_holders(contract_address):
    url = f"{ETHPLORER_API}/getTopTokenHolders/{contract_address}?apiKey={ETHPLORER_KEY}&limit=100"
    try:
        res = requests.get(url)
        data = res.json()
        return data.get("holders", [])
    except Exception as e:
        print(f"Holders alınamadı: {e}")
        return []

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
        f"ZERODAY Balina Tespiti:\n"
        f"Coin: ${coin}\n"
        f"Cüzdan: {address}\n"
        f"Alım: {token_amount:,.0f} adet (~{usd_value:,.0f} USD)\n"
        f"Zaman: {now}\n"
        f"İşlem: https://etherscan.io/tx/{tx_hash}"
    )
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def check_balina_receive():
    for coin, data in COINS.items():
        holders = get_holders(data["contract"])
        price = data["price_usd"]
        for h in holders:
            balance = float(h.get("balance", 0))
            usd_balance = balance * price
            if 1_000_000 <= usd_balance <= 5_000_000:
                address = h.get("address")
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
    print("ZERODAY balina takibi başladı...")
    while True:
        check_balina_receive()
        print("Kontrol tamamlandı. 1 saat bekleniyor...\n")
        time.sleep(3600)

if __name__ == "__main__":
    main()