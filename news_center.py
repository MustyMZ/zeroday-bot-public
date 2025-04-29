import feedparser
import time
import requests
import openai

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]

TELEGRAM_BOT_TOKEN = '7188798462:AAFCnGYv1EZ5rDeNUsG4x-Y2Up9I-pWj8nE'
TELEGRAM_CHAT_ID = '6150871845'

OPENAI_API_KEY = 'BURAYA_OPENAI_API_KEYİNİ_YAZ'

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

openai.api_key = OPENAI_API_KEY

def translate_to_turkish(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional translator that translates English text into natural Turkish."},
                {"role": "user", "content": text}
            ],
            timeout=10
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("Çeviri hatası:", str(e))
        return text

def classify_news(summary):
    summary_lower = summary.lower()
    if any(word in summary_lower for word in ["hack", "lawsuit", "fine", "ban", "investigation", "security issue"]):
        return "SATIM SİNYALİ (Short İşlem Açılabilir)"
    elif any(word in summary_lower for word in ["partnership", "integration", "adoption", "investment", "bullish"]):
        return "ALIM SİNYALİ (Alım Fırsatı Görüldü)"
    else:
        return "NÖTR (Bekle ve Gözlemle)"

def generate_trade_json(action, coin):
    leverage = "3x" if action == "neutral" else f"{str(3 + hash(coin) % 18)}x"
    return {
        "action": action,
        "coins": [coin],
        "leverage": leverage
    }

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            print("Telegram gönderim hatası:", response.text)
    except Exception as e:
        print("Telegram bağlantı hatası:", str(e))

def process_feed():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            title_en = entry.title
            summary_en = entry.summary[:400]
            full_text = f"{title_en} {summary_en}"

            matched_coin = None
            for coin in ALTCOINS:
                if coin.lower() in full_text.lower():
                    matched_coin = coin
                    break

            if matched_coin:
                title_tr = translate_to_turkish(title_en)
                summary_tr = translate_to_turkish(summary_en)
                result = classify_news(summary_en)

                if "ALIM" in result:
                    action = "long"
                    yorum = f"{matched_coin} için ALIM fırsatı görüldü. Long işlem açılabilir."
                elif "SATIM" in result:
                    action = "short"
                    yorum = f"{matched_coin} için SATIŞ fırsatı görüldü. Short işlem açılabilir."
                else:
                    action = "neutral"
                    yorum = f"{matched_coin} için belirgin bir sinyal yok. Beklenmeli."

                trade_json = generate_trade_json(action, matched_coin)

                message = f"""ZERODAY Haber Analizi:
---
Başlık: {title_tr}
Özet: {summary_tr}
Sonuç: {result}
Yorum: {yorum}
İşlem Önerisi: {trade_json}
Kaynak: {entry.link}
"""
                send_to_telegram(message)

if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)