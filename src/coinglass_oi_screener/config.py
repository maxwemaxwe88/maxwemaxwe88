from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Coinglass Open API settings.

    Notes:
    - Coinglass Open API commonly uses header `coinglassSecret` for API key.
    - Make these configurable because Coinglass header names can vary by plan/version.
    """

    model_config = SettingsConfigDict(env_prefix="COINGLASS_", extra="ignore")

    api_base_url: str = "https://open-api.coinglass.com/public/v2"
    api_key: str | None = None
    # If you set COINGLASS_API_KEY_HEADER, only that header will be used.
    api_key_header: str = "coinglassSecret"
    # Optional comma-separated list of headers to try (if api_key_header is default).
    # Env: COINGLASS_API_KEY_HEADERS="coinglassSecret,CG-API-KEY,X-API-KEY"
    api_key_headers: str | None = None
    timeout_s: float = 20.0


def get_settings() -> Settings:
    return Settings()

