"""
Music Discovery Engine (Zero-Scipy / Vercel Optimized)
=====================================================
Serves 100,000 song "sketches" via high-performance Numpy sparse math.
"""

import os
import csv
import numpy as np
from modules.utils import format_movie_response # We'll rename some fields for music

class MusicEngine:
    """The 'Playlist Scribbles' discovery engine."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/", mapping_service=None):
        print("  🎸 Loading Playlist Scribbles (Zero-Scipy)...")
        self.mapping_service = mapping_service

        # 1. Load song metadata
        self.songs = []
        songs_file = os.path.join(data_path, "songs_processed.csv")
        if os.path.exists(songs_file):
            with open(songs_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    row["_idx"] = i 
                    # Map the Spotify headers to our internal 'discover' format
                    # name/artists -> title/info
                    self.songs.append(row)

        # 2. Load Numpy-only CSR Components
        self.data = np.load(os.path.join(model_path, "songs_tfidf_data.npy"))
        self.indices = np.load(os.path.join(model_path, "songs_tfidf_indices.npy"))
        self.indptr = np.load(os.path.join(model_path, "songs_tfidf_indptr.npy"))

        with open(os.path.join(model_path, "songs_tfidf_shape.txt"), "r") as f:
            shape = f.read().split(",")
            self.num_rows = int(shape[0])

        # 3. Create a Row Map for vectorized dot products
        # We pre-calculate which row each index in self.indices belongs to.
        # This allows us to use np.bincount for extremely fast sparse dots.
        self.row_map = np.zeros(len(self.indices), dtype=np.int32)
        for r in range(self.num_rows):
            start, end = self.indptr[r], self.indptr[r+1]
            self.row_map[start:end] = r

        print(f"  ✅ Music Engine ready — {len(self.songs):,} tracks.")

    def search(self, query: str, limit: int = 12) -> list[dict]:
        """Search songs by name or artist."""
        q = query.lower().strip()
        hits = []
        for song in self.songs:
            if q in song["name"].lower() or q in song["artists_clean"].lower() or q in song["album"].lower():
                hits.append(self._format_response(song))
                if len(hits) >= limit: break
        return hits

    def recommend(self, song_id: str, top_n: int = 12, genre: str = None) -> list[dict]:
        """Generate acoustically similar track 'sketches'."""
        # Find index by Spotify ID
        idx = next((s["_idx"] for s in self.songs if s["id"] == song_id), None)
        if idx is None: return []

        # Pure Numpy Sparse Dot Product
        start, end = self.indptr[idx], self.indptr[idx+1]
        row_indices = row_data = [] # fallback
        if start < end:
            row_indices = self.indices[start:end]
            row_data = self.data[start:end]
        
        query_map = dict(zip(row_indices, row_data))
        query_cols_set = set(row_indices)
        
        # ── Vectorized Sparse Dot Product ───────────────────────────────
        # 1. Mask the matrix for columns present in our query song
        mask = np.isin(self.indices, row_indices)
        
        if not np.any(mask):
            return []

        # 2. Get values and row indices for matches
        matching_vals = self.data[mask]
        matching_rows = self.row_map[mask]
        matching_cols = self.indices[mask]
        
        # 3. Calculate weights (query_val * matrix_val)
        # We need the query_val for each matching_cols
        weights = np.array([query_map[c] for c in matching_cols])
        contributions = matching_vals * weights
        
        # 4. Use np.bincount to sum contributions by row
        scores = np.bincount(matching_rows, weights=contributions, minlength=self.num_rows)

        # Top-N partition
        top_indices = np.argpartition(scores, -top_n-1)[-top_n-1:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        top_indices = [i for i in top_indices if i != idx][:top_n]

        return [self._format_response(self.songs[i], scores[i]) for i in top_indices]

    def _format_response(self, song, score=0.0):
        """Maps Spotify metadata to our hand-drawn card format."""
        # We'll use Spotify's ID for metadata fetching later
        return {
            "movieId": song["id"], # We reuse the card ID field for simplicity
            "title": song["name"],
            "artist": song["artists_clean"],
            "album": song["album"],
            "releaseYear": song["year"],
            "tmdbId": -1, # Signals client this isn't a movie
            "spotifyId": song["id"],
            "similarity": round(float(score), 4) if score > 0 else 0,
            "tempo": round(float(song.get("tempo", 0)), 1),
            "energy": round(float(song.get("energy", 0)), 2),
            "danceability": round(float(song.get("danceability", 0)), 2),
            "duration_ms": int(song.get("duration_ms", 0)),
            "explicit": bool(song.get("explicit", False))
        }
