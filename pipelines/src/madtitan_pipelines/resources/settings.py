from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    """Environment-backed settings for private extraction runs."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    local_pdf_mirror: str | None = None
    source_manifest_path: str = "data/source_manifests"
    r2_bucket_name: str | None = None
