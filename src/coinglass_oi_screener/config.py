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
    api_key_header: str = "coinglassSecret"
    timeout_s: float = 20.0


def get_settings() -> Settings:
    return Settings()

