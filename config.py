from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str

    google_credentials_file: str = "credentials.json"
    admin_spreadsheet_id: str
    drive_receipts_folder_id: str = ""
    management_spreadsheet_id: str = ""

    timezone: str = "Europe/Moscow"
    database_url: str = "sqlite+aiosqlite:///data/colizeum.db"


settings = Settings()
