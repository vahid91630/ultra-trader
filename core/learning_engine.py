import os
import joblib
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

MODEL_PATH = "models/rf_model.pkl"

def train_model(data):
    df = pd.DataFrame(data)
    if df.empty or "feature1" not in df.columns:
        print("⚠️ Not enough data for training")
        return
    X = df[["feature1", "feature2"]]
    y = df["label"]
    clf = RandomForestClassifier(n_estimators=50)
    clf.fit(X, y)
    joblib.dump(clf, MODEL_PATH)
    print("✅ Model trained and saved at", MODEL_PATH)

def load_model():
    if os.path.exists(MODEL_PATH):
        print("🔍 Loading existing model")
        return joblib.load(MODEL_PATH)
    print("⚠️ No model file found")
    return None
