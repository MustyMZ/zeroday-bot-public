import asyncio
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ETHERSCAN_API_KEY
from telegram import Bot
import requests

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Telegram mesajı gönderildi:", message)
    except Exception as e:
        print("Telegram mesajı gönderilemedi:", e)

async def fetch_etherscan_whale_transfers():
    print("Veriler taranıyor...")
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address=0x0000000000000000000000000000000000000000&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] != "1":
            print("API hatası:", data.get("message"))
            return

        transfers = data["result"][:3]  # sadece son 3 transferi al
        for transfer in transfers:
            token = transfer["tokenSymbol"]
            value = int(transfer["value"]) / (10 ** int(transfer["tokenDecimal"]))
            whale_address = transfer["from"]
            to_address = transfer["to"]

            message = (
                f"ZERODAY Balina Transferi:\n"
                f"Token: {token}\n"
                f"Miktar: {value:.2f}\n"
                f"Gönderen: {whale_address}\n"
                f"Alıcı: {to_address}"
            )

            await send_telegram_message(message)

    except Exception as e:
        print("Veri çekme hatası:", e)

async def main():
    while True:
        await fetch_etherscan_whale_transfers()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())