# pipeline/storage.py
import sqlite3
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

from app.lyrics_pipeline.config import PipelineConfig
from app.lyrics_pipeline.models import SongRecord

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genius_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    album TEXT,
    year INTEGER,
    plain_lyrics TEXT,
    synced_lyrics TEXT,
    genius_url TEXT,
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_artist ON songs(artist);
CREATE INDEX IF NOT EXISTS idx_year ON songs(year);
CREATE INDEX IF NOT EXISTS idx_has_synced ON songs(synced_lyrics);
"""


class LyricsStorage:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.db_path = config.db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def save(self, record: SongRecord) -> bool:
        """Insert or update a song record. Returns True if new row inserted."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """INSERT INTO songs
                       (genius_id, title, artist, album, year,
                        plain_lyrics, synced_lyrics, genius_url, fetched_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(genius_id) DO UPDATE SET
                           plain_lyrics = COALESCE(excluded.plain_lyrics, plain_lyrics),
                           synced_lyrics = COALESCE(excluded.synced_lyrics, synced_lyrics),
                           fetched_at = excluded.fetched_at
                    """,
                    (
                        record.genius_id, record.title, record.artist,
                        record.album, record.year, record.plain_lyrics,
                        record.synced_lyrics, record.genius_url,
                        record.fetched_at.isoformat(),
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                logger.debug(f"Duplicate skipped: {record.title}")
                return False

    def save_batch(self, records: list[SongRecord]) -> int:
        """Save multiple records. Returns count of new insertions."""
        return sum(1 for r in records if self.save(r))

    def stats(self) -> dict:
        """Get dataset statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
            with_lyrics = conn.execute(
                "SELECT COUNT(*) FROM songs WHERE plain_lyrics IS NOT NULL"
            ).fetchone()[0]
            with_synced = conn.execute(
                "SELECT COUNT(*) FROM songs WHERE synced_lyrics IS NOT NULL"
            ).fetchone()[0]
            artists = conn.execute(
                "SELECT COUNT(DISTINCT artist) FROM songs"
            ).fetchone()[0]
        return {
            "total_songs": total,
            "with_plain_lyrics": with_lyrics,
            "with_synced_lyrics": with_synced,
            "unique_artists": artists,
        }

    # ── Export Methods ──────────────────────────────────────

    def export_jsonl(self, path: Path | None = None) -> Path:
        """Export dataset as JSON Lines (one JSON object per line)."""
        path = path or self.config.export_dir / "lyrics.jsonl"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM songs ORDER BY artist, title").fetchall()

        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                obj = {k: row[k] for k in row.keys() if k != "id"}
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(rows)} songs to {path}")
        return path

    def export_csv(self, path: Path | None = None) -> Path:
        """Export metadata as CSV (lyrics truncated for readability)."""
        path = path or self.config.export_dir / "lyrics.csv"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM songs ORDER BY artist, title").fetchall()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "genius_id", "title", "artist", "album", "year",
                "has_plain", "has_synced", "genius_url",
            ])
            for row in rows:
                writer.writerow([
                    row["genius_id"], row["title"], row["artist"],
                    row["album"], row["year"],
                    bool(row["plain_lyrics"]),
                    bool(row["synced_lyrics"]),
                    row["genius_url"],
                ])

        logger.info(f"Exported {len(rows)} songs to {path}")
        return path

    def export_lrc_files(self, output_dir: Path | None = None) -> int:
        """Export synced lyrics as individual .lrc files."""
        output_dir = output_dir or self.config.export_dir / "lrc"
        output_dir.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT artist, title, synced_lyrics FROM songs "
                "WHERE synced_lyrics IS NOT NULL"
            ).fetchall()

        for row in rows:
            safe_name = f"{row['artist']} - {row['title']}".replace("/", "_")
            lrc_path = output_dir / f"{safe_name}.lrc"
            lrc_path.write_text(row["synced_lyrics"], encoding="utf-8")

        logger.info(f"Exported {len(rows)} .lrc files to {output_dir}")
        return len(rows)
