from functools import lru_cache
from os import getenv
from pathlib import Path


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    service_name = "mage-doc-backend"
    version = "0.1.0"

    def __init__(self) -> None:
        self.env = getenv("MAGEDOC_ENV", "development")
        self.api_host = getenv("MAGEDOC_API_HOST", "127.0.0.1")
        self.api_port = int(getenv("MAGEDOC_API_PORT", "8000"))
        self.workspace_root = Path(getenv("MAGEDOC_WORKSPACE_ROOT", ".magedoc"))
        self.upload_root = self.workspace_root / "uploads"
        self.page_image_root = self.workspace_root / "page-images"
        self.database_url = getenv(
            "MAGEDOC_DATABASE_URL",
            f"sqlite:///{self.workspace_root / 'magedoc.sqlite'}",
        )
        self.upload_max_bytes = int(getenv("MAGEDOC_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024)))
        self.render_zoom = float(getenv("MAGEDOC_RENDER_ZOOM", "2.0"))
        self.cors_origins = _split_csv(
            getenv(
                "MAGEDOC_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
