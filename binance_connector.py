from binance.client import Client
import os

def get_live_price(symbol="BTCUSDT"):
    client = Client()
    price = client.get_symbol_ticker(symbol=symbol)
    return price
