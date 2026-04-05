"""
Content-Based Movie Recommendation Engine (Vercel Optimized)
============================================================
Loads pre-trained TF-IDF assets and serves recommendations via
lazy cosine similarity (single-row dot product against the full matrix).

Optimization: 
  - Removes 'pandas' dependency to fit within Vercel's 500MB limit.
  - Uses native 'csv' module for fast data loading.
"""

import os
import csv
import pickle
import numpy as np
import scipy.sparse as sp
from modules.utils import parse_list_field, format_movie_response


class MovieEngine:
    """Content-based recommendation engine (No-Pandas Edition)."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/", mapping_service=None):
        print("  📦 Loading Content-Based Engine (Vercel Optimized)...")
        self.mapping_service = mapping_service

        # ── 1. Load movie metadata via native CSV ──────────────────
        self.movies = []
        movies_file = os.path.join(data_path, "movies_processed.csv")
        
        if os.path.exists(movies_file):
            with open(movies_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    # Data preparation for search
                    row["movieId"] = int(row["movieId"])
                    row["genres"] = parse_list_field(row["genres"])
                    row["title_norm"] = row["title"].lower().strip()
                    row["_idx"] = i  # Internal tracking for TF-IDF alignment
                    self.movies.append(row)

        # ── 2. Build fast lookup maps ───────────────────────────────
        # movieId → row index in self.movies (and in the TF-IDF matrix)
        self.id_to_idx = {m["movieId"]: i for i, m in enumerate(self.movies)}

        # ── 3. Load TF-IDF assets ──────────────────────────────────
        self.tfidf_matrix = sp.load_npz(os.path.join(model_path, "tfidf_matrix.npz"))

        # Sanity check: matrix rows must match movie count
        assert self.tfidf_matrix.shape[0] == len(self.movies), (
            f"TF-IDF matrix rows ({self.tfidf_matrix.shape[0]}) != "
            f"movies count ({len(self.movies)})"
        )

        print(f"  ✅ Content Engine ready — {len(self.movies):,} movies.")

    # ── Public API ──────────────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search movies by substring match on title. Returns list of dicts."""
        q = query.lower().strip()
        
        # Native Python list filtering instead of pandas mask
        hits = []
        for movie in self.movies:
            if q in movie["title_norm"]:
                hits.append(self._format_with_ids(movie))
                if len(hits) >= limit:
                    break
                    
        return hits

    def recommend(self, movie_id: int, top_n: int = 12) -> list[dict]:
        """
        Generate content-based recommendations for a given movieId.
        Uses scipy.sparse for the dot product similarity.
        """
        idx = self.id_to_idx.get(movie_id)
        if idx is None:
            return []

        # ── Lazy cosine similarity (single-row dot product) ─────────
        target_vector = self.tfidf_matrix[idx]
        sim_scores = target_vector.dot(self.tfidf_matrix.T).toarray().flatten()

        # ── Fast top-N via argpartition ─────────────────────────────
        n_candidates = min(top_n + 1, len(sim_scores))
        top_indices_unsorted = np.argpartition(sim_scores, -n_candidates)[
            -n_candidates:
        ]
        
        # Sort only the small subset using its sim_scores
        top_indices = top_indices_unsorted[
            np.argsort(sim_scores[top_indices_unsorted])[::-1]
        ]
        
        # Remove self-match
        top_indices = top_indices[top_indices != idx][:top_n]

        results = []
        for i in top_indices:
            movie = self.movies[i]
            results.append(
                self._format_with_ids(
                    movie, 
                    score=self._normalize_score(float(sim_scores[i])), 
                    mode="content"
                )
            )

        return results

    def _format_with_ids(self, movie, score=None, mode="content"):
        """Helper to inject IDs from the MappingService into the response."""
        movieId = movie["movieId"]
        
        if self.mapping_service:
             tmdbId = self.mapping_service.get_tmdb_id(movieId)
             imdbId = self.mapping_service.get_imdb_id(movieId)
        else:
             # Legacy fallback (rarely reachable with current service structure)
             tmdbId = int(movie.get("tmdbId", -1))
             imdbId = int(movie.get("imdbId", -1))

        # Standard Movie Response Format
        return format_movie_response(
             {**movie, "tmdbId": tmdbId, "imdbId": imdbId},
             score=score,
             mode=mode
        )

    def _normalize_score(self, score: float) -> float:
        """User-friendly similarity score mapper."""
        if score <= 0: return 0.0
        normalized = 0.65 + (score * 0.7) 
        return round(min(0.98, normalized), 4)
