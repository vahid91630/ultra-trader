from binance.client import Client

client = Client()

def get_live_price(symbol="BTCUSDT"):
    price = client.get_symbol_ticker(symbol=symbol)
    return {
        "symbol": price["symbol"],
        "price": float(price["price"])
    }

def get_all_prices(symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"]):
    return [get_live_price(sym) for sym in symbols]
