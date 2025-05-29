# market_sentiment.py
import requests
from datetime import datetime

BINANCE_API = "https://fapi.binance.com"
COINGECKO_API = "https://api.coingecko.com/api/v3/global"


def get_open_interest(symbol):
    url = f"{BINANCE_API}/futures/data/openInterestHist?symbol={symbol}&period=4h&limit=2"
    try:
        response = requests.get(url)
        data = response.json()
        if len(data) >= 2:
            prev = float(data[-2]['sumOpenInterest'])
            curr = float(data[-1]['sumOpenInterest'])
            change_pct = ((curr - prev) / prev) * 100
            return round(change_pct, 2)
    except:
        return None


def get_long_short_ratio(symbol):
    url = f"{BINANCE_API}/futures/data/topLongShortAccountRatio?symbol={symbol}&period=4h&limit=1"
    try:
        data = requests.get(url).json()
        ratio = float(data[-1]['longShortRatio'])
        return round(ratio, 2)
    except:
        return None


def get_taker_ratio(symbol):
    url = f"{BINANCE_API}/futures/data/takerlongshortRatio?symbol={symbol}&period=4h&limit=1"
    try:
        data = requests.get(url).json()
        ratio = float(data[-1]['buySellRatio'])
        return round(ratio, 2)
    except:
        return None


def get_funding_rate(symbol):
    url = f"{BINANCE_API}/fapi/v1/fundingRate?symbol={symbol}&limit=1"
    try:
        data = requests.get(url).json()
        rate = float(data[-1]['fundingRate']) * 100
        return round(rate, 4)
    except:
        return None


def get_basis(symbol):
    url = f"{BINANCE_API}/futures/data/premiumIndex?symbol={symbol}"
    try:
        data = requests.get(url).json()
        return round(float(data['lastFundingRate']) * 100, 4)
    except:
        return None


def get_dominances():
    try:
        data = requests.get(COINGECKO_API).json()['data']['market_cap_percentage']
        btc_dominance = round(data['btc'], 2)
        usdt_dominance = round(data['usdt'], 2)
        return btc_dominance, usdt_dominance
    except:
        return None, None


def score_metric(value, direction, metric):
    if value is None:
        return 50
    if metric == "open_interest":
        return 80 if value > 2 else 60 if value > 0 else 40
    elif metric == "long_short":
        if direction == "BUY":
            return 80 if value < 1.6 else 60 if value < 2.2 else 40
        else:
            return 80 if value > 2.2 else 60 if value > 1.6 else 40
    elif metric == "taker_ratio":
        if direction == "BUY":
            return 80 if value > 1.3 else 60 if value > 1.0 else 40
        else:
            return 80 if value < 0.7 else 60 if value < 1.0 else 40
    elif metric == "funding":
        if direction == "BUY":
            return 80 if -0.01 <= value <= 0.01 else 60 if value <= 0.02 else 40
        else:
            return 80 if value > 0.02 else 60 if value >= 0.01 else 40
    elif metric == "basis":
        return 80 if value > 0 else 60 if value == 0 else 40
    elif metric == "usdt_dominance":
        if direction == "BUY":
            return 80 if value < 8 else 60 if value < 9 else 40
        else:
            return 80 if value > 9 else 60 if value > 8 else 40
    elif metric == "btc_dominance":
        return 80 if value < 50 else 60 if value < 60 else 40
    return 50


def explain_metric(value, metric):
    if value is None:
        return "Veri alınamadı"
    if metric == "open_interest":
        return f"Open Interest: %{value} → Piyasaya pozisyon girişi"
    elif metric == "long_short":
        return f"Long/Short Ratio: {value} → Trader yönü"
    elif metric == "taker_ratio":
        return f"Taker Buy/Sell: {value} → Alıcı/Satıcı baskısı"
    elif metric == "funding":
        return f"Funding Rate: %{value} → Pozisyon finansmanı"
    elif metric == "basis":
        return f"Basis: %{value} → Futures vs Spot farkı"
    elif metric == "usdt_dominance":
        return f"USDT Dominance: %{value} → Risk iştahı"
    elif metric == "btc_dominance":
        return f"BTC Dominance: %{value} → Altcoin baskısı"
    return ""


def get_market_sentiment_analysis(symbol, direction):
    oi = get_open_interest(symbol)
    ls = get_long_short_ratio(symbol)
    tr = get_taker_ratio(symbol)
    fr = get_funding_rate(symbol)
    bs = get_basis(symbol)
    btc_dom, usdt_dom = get_dominances()

    data = [
        (oi, "open_interest"),
        (ls, "long_short"),
        (tr, "taker_ratio"),
        (fr, "funding"),
        (bs, "basis"),
        (usdt_dom, "usdt_dominance"),
        (btc_dom, "btc_dominance"),
    ]

    explanations = [explain_metric(v, m) for v, m in data]
    scores = [score_metric(v, direction, m) for v, m in data]
    average_score = round(sum(scores) / len(scores), 1)

    if average_score >= 80:
        strength = "GÜÇLÜ ✅"
    elif average_score >= 65:
        strength = "NORMAL ⚠️"
    else:
        strength = "ZAYIF ❌"

    yorum = f"\n🧠 AI Yorum:\nGüven Skoru: %{average_score} → {strength}"
    full_text = "\n📊 Market Sentiment (4H):\n" + "\n".join(explanations) + yorum

    return full_text, average_score