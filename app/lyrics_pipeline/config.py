# pipeline/config.py
from pydantic import BaseModel
from pathlib import Path


class PipelineConfig(BaseModel):
    genius_token: str
    db_path: Path = Path("data/lyrics.db")
    export_dir: Path = Path("data/exports")
    request_delay: float = 1.5        # seconds between Genius API calls
    max_retries: int = 3
    batch_size: int = 50              # songs per artist batch
    synced_providers: list[str] = ["musixmatch", "lrclib"]

    def ensure_dirs(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
