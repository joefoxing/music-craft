# pipeline/models.py
from pydantic import BaseModel, Field
from datetime import datetime


class SongRecord(BaseModel):
    genius_id: int | None = None
    title: str
    artist: str
    album: str | None = None
    year: int | None = None
    plain_lyrics: str | None = None
    synced_lyrics: str | None = None     # LRC format
    genius_url: str | None = None
    fetched_at: datetime = Field(default_factory=datetime.now)

    @property
    def has_synced(self) -> bool:
        return self.synced_lyrics is not None

    @property
    def search_term(self) -> str:
        return f"{self.title} {self.artist}"
