# pipeline/fetcher.py
import time
import logging
from typing import Generator

import lyricsgenius
import syncedlyrics

from app.lyrics_pipeline.config import PipelineConfig
from app.lyrics_pipeline.models import SongRecord

logger = logging.getLogger(__name__)


class LyricsFetcher:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.genius = lyricsgenius.Genius(
            config.genius_token,
            verbose=False,
            remove_section_headers=True,
            retries=config.max_retries,
        )
        # Skip live/remix/edit variants to keep dataset clean
        self.genius.excluded_terms = [
            "(Remix)", "(Live)", "(Demo)",
            "(Edit)", "(Skit)", "(Interlude)",
        ]

    def fetch_artist_songs(self, artist_name: str, max_songs: int = 50) -> Generator[SongRecord, None, None]:
        """Fetch all songs for an artist from Genius, then enrich with synced lyrics."""
        logger.info(f"Fetching songs for: {artist_name}")

        artist = self.genius.search_artist(
            artist_name,
            max_songs=max_songs,
            sort="popularity",
            get_full_info=False,
        )
        if not artist:
            logger.warning(f"Artist not found: {artist_name}")
            return

        for song in artist.songs:
            record = SongRecord(
                genius_id=getattr(song, "id", None) or getattr(song, "genius_id", None) or (song._body.get("id") if hasattr(song, "_body") else None),
                title=song.title,
                artist=artist.name,
                album=getattr(song, "album", None),
                year=self._extract_year(song),
                plain_lyrics=self._clean_lyrics(song.lyrics),
                genius_url=song.url,
            )

            # Enrich with synced lyrics
            record.synced_lyrics = self._fetch_synced(record.title, record.artist)

            logger.info(
                f"  ✓ {record.title}"
                f"{' [+synced]' if record.has_synced else ''}"
            )
            yield record

            time.sleep(self.config.request_delay)

    def fetch_single(self, title: str, artist: str) -> SongRecord:
        """Fetch a single song by title and artist."""
        song = self.genius.search_song(title, artist)

        # Use the actual title/artist Genius returns, not the raw search query
        actual_title  = (getattr(song, "title", None) or title) if song else title
        actual_artist = title  # fallback: treat the query as artist name
        if song:
            primary = getattr(song, "primary_artist", None) or getattr(song, "artist", None)
            if primary:
                actual_artist = getattr(primary, "name", None) or str(primary)
            elif hasattr(song, "_body"):
                actual_artist = (song._body.get("primary_artist") or {}).get("name", title)

        genius_id = (getattr(song, "id", None) or getattr(song, "genius_id", None) or
                     (song._body.get("id") if hasattr(song, "_body") else None)) if song else None

        record = SongRecord(
            genius_id=genius_id,
            title=actual_title,
            artist=actual_artist,
            plain_lyrics=self._clean_lyrics(song.lyrics) if song else None,
            genius_url=song.url if song else None,
        )
        record.synced_lyrics = self._fetch_synced(actual_title, actual_artist)
        return record

    def _fetch_synced(self, title: str, artist: str) -> str | None:
        """Try to get LRC-format synced lyrics from multiple providers."""
        try:
            lrc = syncedlyrics.search(
                f"{title} {artist}",
                synced_only=True,
                providers=self.config.synced_providers,
            )
            return lrc
        except Exception as e:
            logger.debug(f"  No synced lyrics for {title}: {e}")
            return None

    def _clean_lyrics(self, raw: str | None) -> str | None:
        if not raw:
            return None
        # Remove the "N ContributorsSong Lyrics" header Genius prepends
        lines = raw.strip().split("\n")
        if lines and "Lyrics" in lines[0]:
            lines = lines[1:]
        # Remove trailing "Embed" or contributor text
        if lines and ("Embed" in lines[-1] or "You might also like" in lines[-1]):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @staticmethod
    def _extract_year(song) -> int | None:
        try:
            date_str = (
                getattr(song, "year", None)
                or getattr(song, "release_date", None)
                or (song._body.get("release_date_for_display") if hasattr(song, "_body") else None)
            )
            if date_str:
                return int(str(date_str)[:4])
        except (ValueError, TypeError):
            pass
        return None
