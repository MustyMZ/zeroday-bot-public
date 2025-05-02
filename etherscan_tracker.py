import requests
import time
import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ETHERSCAN_API_KEY
from telegram import Bot

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# İzlenecek token contract adresleri (örnek: USDT, PEPE, vs.)
TOKEN_CONTRACTS = {
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    # Diğer tokenlar da buraya eklenebilir
}

EXCLUDED_ADDRESSES = [
    # Buraya kendi cüzdan adreslerini veya önemsiz cüzdanları ekleyebilirsin
]

THRESHOLD_USDT = 100000  # Minimum takip edilecek transfer miktarı

def get_token_transfers(token_name, contract_address):
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=5&sort=desc&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get("result", [])
            return data
    except Exception as e:
        print(f"Etherscan bağlantı hatası: {e}")
    return []

def send_telegram_alert(token_name, amount_usdt, direction, tx_hash):
    now = datetime.datetime.utcnow().strftime("%H:%M UTC - %d/%m/%Y")
    message = (
        f"ZERODAY Balina Tespiti:\n"
        f"Coin: ${token_name}\n"
        f"Transfer: {int(amount_usdt):,} USDT\n"
        f"Yön: {direction}\n"
        f"Tahmini Aksiyon: {'SHORT' if direction == 'Cüzdandan Borsaya (Satış Hazırlığı)' else 'LONG'} Sinyali\n"
        f"Zaman: {now}\n"
        f"Kaynak: https://etherscan.io/tx/{tx_hash}"
    )
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def main():
    print("Etherscan balina takibi başladı...")
    processed_tx = set()

    while True:
        for token_name, contract in TOKEN_CONTRACTS.items():
            transfers = get_token_transfers(token_name, contract)
            for tx in transfers:
                tx_hash = tx["hash"]
                if tx_hash in processed_tx:
                    continue

                from_addr = tx["from"].lower()
                to_addr = tx["to"].lower()
                value_raw = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
                if value_raw < THRESHOLD_USDT:
                    continue

                if from_addr in EXCLUDED_ADDRESSES or to_addr in EXCLUDED_ADDRESSES:
                    continue

                direction = ""
                if "binance" in to_addr:
                    direction = "Cüzdandan Borsaya (Satış Hazırlığı)"
                elif "binance" in from_addr:
                    direction = "Borsadan Cüzdana (Alım Hazırlığı)"
                else:
                    direction = "Cüzdandan Borsaya (Satış Hazırlığı)"

                send_telegram_alert(token_name, value_raw, direction, tx_hash)
                processed_tx.add(tx_hash)

        print("Tüm tokenlar kontrol edildi. 60 sn bekleniyor...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()