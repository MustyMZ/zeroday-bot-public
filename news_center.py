import feedparser
import time
import requests
import os
import random
from dotenv import load_dotenv
import openai

load_dotenv()

# API KEY'LER
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# ALTCOIN LİSTESİ
ALTCOINS = ["SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "ARB", "OP", "MATIC", "SUI", "APE", "LTC", "TRX", "DOT", "ATOM"]

# RSS KAYNAKLARI
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

# TELEGRAM MESAJ GÖNDER
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram Hatası:", str(e))

# OPENAI İLE HABERİ TÜRKÇEYE ÇEVİR VE YORUM YAP
def analyze_and_translate(title, summary):
    try:
        messages = [
            {"role": "system", "content": "Sen kripto para uzmanı bir Türk analizörsün."},
            {"role": "user", "content": f"Bu haberin başlığını ve özetini Türkçeye çevir ve analiz et:\n\nBaşlık: {title}\n\nÖzet: {summary}\n\n1) Bu haber hangi coini etkiler?\n2) Bu coin için işlem yönü (long/short/neutral) ne olmalı?\n3) Kaldıraç önerin (3x-20x) ne olur?\nYanıtı sadece şu JSON formatında ver:\n{{\"action\": \"long/short/neutral\", \"coins\": [\"...\"], \"leverage\": \"...x\"}}"}
        ]
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Haber analiz edilemedi. Hata: {str(e)}"

# HABERLERİ İŞLE
def process_feed():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:
            title = entry.title
            summary = entry.summary[:500]
            result_json = analyze_and_translate(title, summary)

            message = f"""ZERODAY Haber Analizi:
---
Başlık: {title}
Özet: {summary}
Sonuç: {result_json}
Kaynak: {entry.link}
"""
            send_to_telegram(message)

# DÖNGÜ
if __name__ == "__main__":
    while True:
        print("Yeni haberler taranıyor...")
        process_feed()
        print("1 saat uyku...")
        time.sleep(3600)