from analyzer import generate_signal, get_price
from price_watcher import detect_spike
import asyncio
from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID

bot = Bot(token=TELEGRAM_TOKEN)

async def send_to_telegram(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def format_telegram_message(symbol, price, trend, momentum, signal):
    from datetime import datetime
    message_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    message = f"""{symbol} Teknik Durum ({message_time}):
Fiyat: {price:,.2f} USDT
Trend: {trend}
Momentum: {momentum}
Sonuç: {signal}

Açıklama: Tüm göstergeler yükselişi destekliyor.
Kendi risk analizinizle alım düşünebilirsiniz.
"""
    return message

async def main():
    coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    for coin in coins:
        try:
            price = get_price(coin)
            trend_signal, momentum_signal, final_signal = generate_signal(coin)

            msg = format_telegram_message(coin, price, trend_signal, momentum_signal, final_signal)
            print(msg)
            await send_to_telegram(msg)

            # Ani fiyat değişimi kontrolü
            spike = detect_spike(coin)
            if "ANI HAREKET" in spike:
                await send_to_telegram(spike)

        except Exception as e:
            print(f"{coin} için hata oluştu: {e}")

async def loop_forever():
    while True:
        await main()
        print("1 saat uykuya geçiliyor...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(loop_forever())
