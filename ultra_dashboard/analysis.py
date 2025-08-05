import pandas as pd

def analyze(data):
    df = pd.DataFrame(data)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna()

    stats = {
        "count": len(df),
        "average": round(df["price"].mean(), 2),
        "
