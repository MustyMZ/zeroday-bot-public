from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET

# Binance API bağlantısı
try:
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
except Exception as e:
    print(f"API bağlantısı başarısız: {e}")
    client = None

# Hesap bilgisi almak
def get_account_info():
    if client:
        try:
            info = client.get_account()
            print(info)
            return info
        except Exception as e:
            print(f"Hesap bilgisi alınamadı: {e}")
    else:
        print("Client başlatılamadığı için işlem yapılamıyor.")

# Belirli bir coin bakiyesi almak
def get_balance(asset='USDT'):
    if client:
        try:
            balance = client.get_asset_balance(asset=asset)
            print(f"{asset} Bakiyesi: {balance['free']}")
            return balance['free']
        except Exception as e:
            print(f"{asset} bakiyesi alınamadı: {e}")
    else:
        print("Client başlatılamadığı için işlem yapılamıyor.")

if __name__ == "__main__":
    get_balance()
    get_account_info()
