import os

class APIManager:
    def __init__(self):
        self.openai = os.getenv("OPENAI_API_KEY")
        self.av = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.newsapi = os.getenv("NEWSAPI_KEY")
        self.hf = os.getenv("HUGGINGFACE_API_KEY")

    def check_keys(self):
        missing = []
        for name, key in [("OpenAI", self.openai), ("AlphaVantage", self.av),
                          ("NewsAPI", self.newsapi), ("HuggingFace", self.hf)]:
            if not key:
                missing.append(name)
        if missing:
            print("⚠️ Missing API keys for:", ", ".join(missing))
        else:
            print("✅ All configured API keys loaded")
