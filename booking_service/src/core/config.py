from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    project_name: str = "booking_service"
    app_host: str = "0.0.0.0"
    app_port: int = 8010

    postgres_db: str = "booking"
    postgres_user: str = "app"
    postgres_password: str = "123qwe"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5435

    auth_jwt_secret: str = "change_me"
    auth_jwt_algorithm: str = "HS256"

    movies_api_url: str = "http://127.0.0.1:8000"
    movies_api_validate: bool = False

    @property
    def database_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
