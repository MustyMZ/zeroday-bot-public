def turtle_trading_strategy():
    # Binance üzerinden BTC/USDT ticaret verisini al
    market_data = client.get_ticker(symbol='BTCUSDT')
    print(f"Market verisi alındı: {market_data}")
    
    last_price = float(market_data['lastPrice'])

    # Burada basit bir fiyat kontrolü yapalım: Örneğin 40,000 USD'yi geçtiğinde alım yapalım
    if last_price > 40000:
        print(f"Fiyat {last_price} > 40,000! BTC al!")
        # Burada Binance API üzerinden işlem yapılabilir
    else:
        print(f"Fiyat {last_price} < 40,000, bekleniyor...")
