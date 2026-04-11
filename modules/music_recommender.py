"""
Music Discovery Engine (Zero-Scipy / Vercel Optimized)
=====================================================
Serves 100,000 song "sketches" via high-performance Numpy sparse math.
"""

import os
import csv
import numpy as np
from sys import intern
from modules.utils import format_movie_response # We'll rename some fields for music

class MusicEngine:
    """The 'Playlist Scribbles' discovery engine."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/", mapping_service=None):
        print("  🎸 Loading Playlist Scribbles (Pandas Optimization)...")
        self.mapping_service = mapping_service

        # 1. Load song metadata via Pandas
        import pandas as pd
        songs_file = os.path.join(data_path, "songs_processed.csv")
        self.df = pd.read_csv(songs_file)
        self.df["_idx"] = np.arange(len(self.df))
        self.df["name_norm"] = self.df["name"].str.lower()
        self.df["artist_norm"] = self.df["artists_clean"].str.lower()
        
        # O(1) ID lookup map
        self.id_to_idx = dict(zip(self.df["id"], self.df["_idx"]))

        # 2. Load Numpy-only CSR Components
        self.data = np.load(os.path.join(model_path, "songs_tfidf_data.npy"))
        self.indices = np.load(os.path.join(model_path, "songs_tfidf_indices.npy"))
        self.indptr = np.load(os.path.join(model_path, "songs_tfidf_indptr.npy"))

        with open(os.path.join(model_path, "songs_tfidf_shape.txt"), "r") as f:
            shape = f.read().split(",")
            self.num_rows = int(shape[0])

        # 3. Create a Row Map for vectorized dot products
        self.row_map = np.zeros(len(self.indices), dtype=np.int32)
        for r in range(self.num_rows):
            start, end = self.indptr[r], self.indptr[r+1]
            self.row_map[start:end] = r

        print(f"  ✅ Music Engine ready — {len(self.df):,} tracks.")
        
        # O4: Pre-compute fuzzy search pool
        self._fuzzy_choices = (
            self.df["name"].iloc[:3000].tolist() + 
            self.df["artists_clean"].iloc[:500].unique().tolist()
        )

    def search(self, query: str, limit: int = 15) -> tuple[list[dict], str | None]:
        """Vectorized search songs by name or artist with fuzzy fallback."""
        from modules.utils import get_fuzzy_suggestion
        q = query.lower().strip()
        mask = self.df["name_norm"].str.contains(q, na=False) | self.df["artist_norm"].str.contains(q, na=False)
        hits = self.df[mask].head(limit)
        results = [self._format_response(row.to_dict()) for _, row in hits.iterrows()]
        
        suggestion = None
        if not results:
            suggestion = get_fuzzy_suggestion(query, self._fuzzy_choices)
            
        return results, suggestion

    def recommend(self, song_id: str, top_n: int = 12, genre: str = None) -> list[dict]:
        """Generate acoustically similar track 'sketches' via O(1) lookup."""
        idx = self.id_to_idx.get(song_id)
        if idx is None: return []

        # Vectorized Sparse Dot Product
        start, end = self.indptr[idx], self.indptr[idx+1]
        if start >= end: return []
        row_indices = self.indices[start:end]
        row_data = self.data[start:end]
        query_map = dict(zip(row_indices, row_data))
        
        mask = np.isin(self.indices, row_indices)
        if not np.any(mask): return []

        matching_vals = self.data[mask]
        matching_rows = self.row_map[mask]
        matching_cols = self.indices[mask]
        
        weights = np.array([query_map[c] for c in matching_cols])
        contributions = matching_vals * weights
        scores = np.bincount(matching_rows, weights=contributions, minlength=self.num_rows)

        # Top-N partition
        top_indices = np.argpartition(scores, -top_n-1)[-top_n-1:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        top_indices = [i for i in top_indices if i != idx][:top_n]

        return [self._format_response(self.df.iloc[i].to_dict(), scores[i]) for i in top_indices]

    def discover(self, limit: int = 24) -> list[dict]:
        """Return a random selection of songs via Numpy sampling."""
        sample_indices = np.random.choice(len(self.df), min(len(self.df), limit), replace=False)
        rows = self.df.iloc[sample_indices]
        return [self._format_response(row.to_dict()) for _, row in rows.iterrows()]

    def _format_response(self, song, score=0.0):
        """Maps Spotify metadata to our hand-drawn card format."""
        return {
            "movieId": song["id"],
            "title": song["name"],
            "artist": song["artists_clean"],
            "album": song.get("album", "Unknown"),
            "releaseYear": song["year"],
            "tmdbId": -1,
            "spotifyId": song["id"],
            "similarity": round(float(score), 4) if score > 0 else 0,
            "tempo": round(float(song.get("tempo", 0)), 1),
            "energy": round(float(song.get("energy", 0)), 2),
            "danceability": round(float(song.get("danceability", 0)), 2)
        }
