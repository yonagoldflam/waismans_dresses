from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config(BaseSettings):
    DSQL_CLUSTER_USER: str
    DSQL_CLUSTER_ENDPOINT: str
    ADMIN_SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")

config = Config()