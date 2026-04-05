import os
import pandas as pd
from typing import Dict, Optional

class MappingService:
    """
    High-performance ID mapping service for MovieLens IDs to TMDB/IMDB IDs.
    Uses O(1) dictionary lookups instead of DataFrame joins.
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
        print(f"  🔗 Loading ID Mappings from {self.links_file}...")
        if not os.path.exists(self.links_file):
            print(f"  ⚠️  Mapping file not found: {self.links_file}")
            return

        # Load only necessary columns with correct dtypes
        df = pd.read_csv(
            self.links_file,
            usecols=["movieId", "imdbId", "tmdbId"],
            dtype={"movieId": "int32", "imdbId": "int32", "tmdbId": "int32"}
        )

        # Build fast dictionaries
        self.movie_to_tmdb = dict(zip(df["movieId"], df["tmdbId"]))
        self.movie_to_imdb = dict(zip(df["movieId"], df["imdbId"]))
        self.tmdb_to_movie = dict(zip(df["tmdbId"], df["movieId"]))
        
        print(f"  ✅ Mapping Service ready — {len(self.movie_to_tmdb):,} IDs mapped.")

    def get_tmdb_id(self, movie_id: int) -> int:
        """Translates MovieLens movieId to TMDB tmdbId instantly."""
        return self.movie_to_tmdb.get(movie_id, -1)

    def get_imdb_id(self, movie_id: int) -> int:
        """Translates MovieLens movieId to IMDB imdbId instantly."""
        return self.movie_to_imdb.get(movie_id, -1)

    def get_movie_id(self, tmdb_id: int) -> int:
        """Translates TMDB tmdbId back to MovieLens movieId instantly."""
        return self.tmdb_to_movie.get(tmdb_id, -1)
