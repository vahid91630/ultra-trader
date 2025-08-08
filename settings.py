import os
from dataclasses import dataclass
from typing import Optional, Sequence

# Load local .env in development; harmless on Railway
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

def _get(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)

def _first(names: Sequence[str], default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty env var from a list of names."""
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default

@dataclass(frozen=True)
class Settings:
    # Common API keys (optional unless your logic requires them)
    API_KEY: Optional[str] = _get("API_KEY")
    COINDESK_API_KEY: Optional[str] = _first(["COINDESK_API_KEY", "COINDESK_KEY", "COINDESK"])  # tolerate variants
    NEWS_API_KEY: Optional[str] = _first(["NEWS_API_KEY", "NEWSAPI_KEY", "NEWS_API"])  # tolerate variants
    POLYGON_API_KEY: Optional[str] = _first(["POLYGON_API_KEY", "POLYGON_KEY"])  # tolerate variants
    SANTIMENT_API_KEY: Optional[str] = _first(["SANTIMENT_API_KEY", "SANTIMENT_KEY"])  # tolerate variants
    TAAPI_API_KEY: Optional[str] = _first(["TAAPI_API_KEY", "TAAPI_KEY"])  # tolerate variants
    TOKENMETRICS_API_KEY: Optional[str] = _first(["TOKENMETRICS_API_KEY", "TOKENMETRICS_KEY"])  # tolerate variants

    # MongoDB connection (required)
    MONGODB_URI: Optional[str] = _first(["MONGODB_URI", "MONGODB_URL", "MONGODB", "MONGODB_SRV"])  # tolerate variants

    # Telegram & Twitter
    TELEGRAM_TOKEN: Optional[str] = _first(["TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN"])  # tolerate variants
    TWITTER_BEARER_TOKEN: Optional[str] = _first(["TWITTER_BEARER_TOKEN", "TWITTER_TOKEN", "TWITTER_BEARER"])  # tolerate variants

    # Flask/Gunicorn & runtime
    SECRET_KEY: str = _get("SECRET_KEY", "change-me")
    PORT: int = int(os.getenv("PORT", "5000"))  # Railway provides PORT
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}

    def validate(self) -> None:
        # Validate required pieces early to fail fast in deploy logs
        if not self.MONGODB_URI:
            raise RuntimeError(
                "Missing required environment variable: MONGODB_URI (or MONGODB_URL/MONGODB/MONGODB_SRV)."
            )

# Singleton settings object to be used across the app
settings = Settings()
settings.validate()

__all__ = ["Settings", "settings"]