# pipeline/runner.py
import logging
from tqdm import tqdm

from app.lyrics_pipeline.config import PipelineConfig
from app.lyrics_pipeline.fetcher import LyricsFetcher
from app.lyrics_pipeline.storage import LyricsStorage
from app.lyrics_pipeline.models import SongRecord

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self, config: PipelineConfig):
        self.config = config
        config.ensure_dirs()
        self.fetcher = LyricsFetcher(config)
        self.storage = LyricsStorage(config)

    def ingest_artist(self, artist_name: str, max_songs: int = 50) -> int:
        """Fetch and store all songs for an artist. Returns count saved."""
        saved = 0
        songs = self.fetcher.fetch_artist_songs(artist_name, max_songs)
        for record in songs:
            if self.storage.save(record):
                saved += 1
        logger.info(f"Saved {saved} songs for {artist_name}")
        return saved

    def ingest_artists(self, artist_names: list[str], max_songs_each: int = 50):
        """Batch ingest multiple artists with progress bar."""
        total_saved = 0
        for name in tqdm(artist_names, desc="Artists", unit="artist"):
            try:
                count = self.ingest_artist(name, max_songs_each)
                total_saved += count
            except Exception as e:
                logger.error(f"Failed on {name}: {e}")
                continue

        stats = self.storage.stats()
        logger.info(
            f"\n{'='*40}\n"
            f"Pipeline complete.\n"
            f"  Total songs:  {stats['total_songs']}\n"
            f"  Plain lyrics: {stats['with_plain_lyrics']}\n"
            f"  Synced (LRC): {stats['with_synced_lyrics']}\n"
            f"  Artists:      {stats['unique_artists']}\n"
            f"{'='*40}"
        )
        return stats

    def ingest_song(self, title: str, artist: str) -> SongRecord:
        """Fetch and store a single song."""
        record = self.fetcher.fetch_single(title, artist)
        self.storage.save(record)
        return record

    def export_all(self):
        """Export dataset in all formats."""
        self.storage.export_jsonl()
        self.storage.export_csv()
        lrc_count = self.storage.export_lrc_files()
        logger.info(f"Exports complete ({lrc_count} LRC files)")
