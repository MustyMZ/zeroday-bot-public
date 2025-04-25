# signal_center.py
from analyzer import generate_signal
from price_watcher import detect_spike
import asyncio
from telegram import Bot

TELEGRAM_TOKEN = "8004645629:AAEWNB1YTPHUZnKLD_lHJVWwjPCEfoDfNoY"
CHAT_ID = 6150871845  # Alternatif olarak kullanıcı ID de olur
bot = Bot(token=TELEGRAM_TOKEN)

async def send_to_telegram(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

async def main():
    coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    for coin in coins:
        try:
            analysis = generate_signal(coin)
            spike = detect_spike(coin)

            print(analysis)
            print(spike)

            await send_to_telegram(analysis)
            if "ANI HAREKET" in spike:
                await send_to_telegram(spike)

        except Exception as e:
            print(f"{coin} için hata oluştu: {e}")

# Tek seferlik çalıştır
if __name__ == "__main__":
    asyncio.run(main())
