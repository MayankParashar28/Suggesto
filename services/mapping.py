import os
import csv
from typing import Dict, Optional

class MappingService:
    """
    High-performance ID mapping service for MovieLens IDs to TMDB/IMDB IDs.
    Uses O(1) dictionary lookups via native CSV module (Vercel Optimized).
    """
    def __init__(self, data_path: str = "processed/"):
        self.data_path = data_path
        self.links_file = os.path.join(data_path, "links_processed.csv")
        
        # O(1) Lookups
        self.movie_to_tmdb: Dict[int, int] = {}
        self.movie_to_imdb: Dict[int, int] = {}
        self.tmdb_to_movie: Dict[int, int] = {}
        
        self._load_mappings()

    def _load_mappings(self):
        print(f"  🔗 Loading ID Mappings from {self.links_file} (Native CSV)...")
        if not os.path.exists(self.links_file):
            print(f"  ⚠️  Mapping file not found: {self.links_file}")
            return

        # Build fast dictionaries using native CSV module to save ~100MB (no pandas)
        try:
            with open(self.links_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        mid = int(row["movieId"])
                        tid = int(row["tmdbId"]) if row["tmdbId"] and row["tmdbId"] != '-1' else -1
                        iid = int(row["imdbId"]) if row["imdbId"] and row["imdbId"] != '-1' else -1
                        
                        self.movie_to_tmdb[mid] = tid
                        self.movie_to_imdb[mid] = iid
                        self.tmdb_to_movie[tid] = mid
                    except (ValueError, KeyError):
                        continue
            print(f"  ✅ Mapping Service ready — {len(self.movie_to_tmdb):,} IDs mapped.")
        except Exception as e:
            print(f"  ❌ Failed to load mappings: {e}")

    def get_tmdb_id(self, movie_id: int) -> int:
        """Translates MovieLens movieId to TMDB tmdbId instantly."""
        return self.movie_to_tmdb.get(movie_id, -1)

    def get_imdb_id(self, movie_id: int) -> int:
        """Translates MovieLens movieId to IMDB imdbId instantly."""
        return self.movie_to_imdb.get(movie_id, -1)

    def get_movie_id(self, tmdb_id: int) -> int:
        """Translates TMDB tmdbId back to MovieLens movieId instantly."""
        return self.tmdb_to_movie.get(tmdb_id, -1)
