from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "B-Star"
    debug: bool = True
    jwt_secret: str = "change-me-in-local-demo-please-use-32bytes+"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    data_dir: Path = Path("./data")
    default_llm_base_url: str = "https://api.deepseek.com/v1"
    default_llm_model: str = "deepseek-v4-pro"
    default_llm_fast_model: str = "deepseek-v4-flash"
    default_llm_api_key: str = ""
    database_url: str = ""
    mysql_connect_timeout: int = 5
    mysql_fallback_sqlite: bool = True
    trial_enabled: bool = True
    trial_username: str = "demo"
    trial_anime_username: str = "demo-anime"
    trial_pet_username: str = "demo-pet"
    trial_reset_minutes: int = 10
    trial_jwt_expire_minutes: int = 120
    trial_login_requests_per_minute: int = 20
    trial_generation_requests_per_window: int = 5
    trial_generation_window_seconds: int = 600
    trial_generation_max_concurrency: int = 2

    def model_post_init(self, __context) -> None:
        if not self.data_dir.is_absolute():
            self.data_dir = (_BACKEND_DIR / self.data_dir).resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "bstar.db"

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url.strip():
            return self.database_url.strip()
        return f"sqlite:///{self.db_path}"

    @property
    def secrets_path(self) -> Path:
        return self.data_dir / "secrets.json"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"


settings = Settings()
