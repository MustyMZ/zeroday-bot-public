import feedparser
import time
import requests
import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APT"]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/",
    "https://news.bitcoin.com/feed/",
    "https://u.today/rss",
    "https://coinpedia.org/feed/",
    "https://ambcrypto.com/feed/"
]

def translate_to_turkish(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bu metni Türkçeye çevir."},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Çeviri hatası: {e}"

def classify_news(summary):
    summary_lower = summary.lower()
    if any(word in summary_lower for word in ["hack", "lawsuit", "fine", "ban", "investigation"]):
        return "SATIM SİNYALİ (Short İşlem Açılabilir)"
    elif any(word in summary_lower for word in ["partnership", "integration", "adoption", "listing", "growth"]):
        return "ALIM SİNYALİ (Alım Fırsatı Görüldü)"
    else:
        return "NÖTR (Bekle ve Gözlemle)"

def extract_affected_coin(summary):
    for coin in ALTCOINS:
        if coin.lower() in summary.lower():
            return coin
    return "BTC"

def generate_json_strategy(signal, coin):
    action = "short" if "SATIM" in signal else "long" if "ALIM" in signal else "neutral"
    leverage = f"{str(3 + hash(coin) % 18)}x"
    return {
        "action": action,
        "coins": [coin],
        "leverage": leverage
    }

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def fetch_and_process_news():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:
            title = entry.title
            summary = entry.summary
            link = entry.link

            title_tr = translate_to_turkish(title)
            summary_tr = translate_to_turkish(summary)

            signal = classify_news(summary_tr)
            affected_coin = extract_affected_coin(summary_tr)
            json_data = generate_json_strategy(signal, affected_coin)

            message = f"""
<b>ZERODAY Haber Analizi:</b>
<b>Başlık:</b> {title_tr}
<b>Özet:</b> {summary_tr}
<b>Sonuç:</b> {signal}
<b>Yorum:</b> {affected_coin} için analiz sonucu: {signal}
<b>Kaynak:</b> {link}

<b>JSON Strateji:</b>
<pre>
{json_data}
</pre>
            """.strip()

            send_to_telegram(message)
            time.sleep(10)

if __name__ == "__main__":
    while True:
        fetch_and_process_news()
        time.sleep(3600)