from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str
    google_api_key: str
    secret_key: str = "dev-secret-key-change-me"

    db_path: str = "./data/app.db"
    chroma_dir: str = "./chroma_db"
    chroma_collection: str = "giao_trinh_c"

    embedding_model: str = "models/gemini-embedding-001"
    groq_model: str = "llama-3.3-70b-versatile"

    session_https_only: bool = False


settings = Settings()
