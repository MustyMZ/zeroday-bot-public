from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET

# Binance API bağlantısı
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Market bilgisi almak
def get_account_info():
    info = client.get_account()
    print(info)

# Örnek işlem: Balans (Bakiyeleri çekmek)
def get_balance():
    balance = client.get_asset_balance(asset='USDT')
    print(f"USDT Bakiyesi: {balance['free']}")

if __name__ == "__main__":
    get_balance()
    get_account_info()
