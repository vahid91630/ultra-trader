import os
from dataclasses import dataclass
from typing import Optional

# Load .env in local development; harmless in production (Railway)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def _get(name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    """Fetch an environment variable.

    - required=True: raise if missing/empty
    - default: used only when variable is absent or empty and required=False
    """
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

@dataclass(frozen=True)
class Settings:
    # API keys (optional unless your feature depends on them)
    API_KEY: Optional[str] = _get("API_KEY", required=False)
    COINDESK_API_KEY: Optional[str] = _get("COINDESK_API_KEY", required=False)
    NEWS_API_KEY: Optional[str] = _get("NEWS_API_KEY", required=False)
    POLYGON_API_KEY: Optional[str] = _get("POLYGON_API_KEY", required=False)
    SANTIMENT_API_KEY: Optional[str] = _get("SANTIMENT_API_KEY", required=False)
    TAAPI_API_KEY: Optional[str] = _get("TAAPI_API_KEY", required=False)
    TOKENMETRICS_API_KEY: Optional[str] = _get("TOKENMETRICS_API_KEY", required=False)
    TWITTER_BEARER_TOKEN: Optional[str] = _get("TWITTER_BEARER_TOKEN", required=False)

    # Databases / secrets
    MONGODB_URI: Optional[str] = _get("MONGODB_URI", required=True)
    SECRET_KEY: str = _get("SECRET_KEY", required=False, default="change-me") or "change-me"

    # Platform
    PORT: int = int(os.getenv("PORT", "5000"))


settings = Settings()

__all__ = ["settings", "Settings"]
