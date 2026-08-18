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
    default_llm_model: str = "deepseek-chat"

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
    def secrets_path(self) -> Path:
        return self.data_dir / "secrets.json"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"


settings = Settings()
