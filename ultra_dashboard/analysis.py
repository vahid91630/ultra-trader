import pandas as pd

def analyze(data):
    df = pd.DataFrame(data)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna()

    stats = {
        "count": len(df),
        "average": round(df["price"].mean(), 2),
        "max": df["price"].max(),
        "min": df["price"].min(),
        "last": df["price"].iloc[-1],
        "first": df["price"].iloc[0],
        "change": round(((df["price"].iloc[-1] - df["price"].iloc[0]) / df["price"].iloc[0]) * 100, 2)
    }

    return df, stats
