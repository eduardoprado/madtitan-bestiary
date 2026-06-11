from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    """Environment-backed settings for private extraction runs."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://madtitan:madtitan@localhost:5432/madtitan_bestiary"
    local_pdf_mirror: str | None = None
    r2_bucket_name: str | None = None
