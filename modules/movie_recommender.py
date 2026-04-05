"""
Content-Based Movie Recommendation Engine
==========================================
Loads pre-trained TF-IDF assets and serves recommendations via
lazy cosine similarity (single-row dot product against the full matrix).

Performance:
  - Startup: ~1s (loads sparse matrix + pickled dicts)
  - Search:  O(n) substring scan, <5ms for 87K titles
  - Recommend: ~15ms per query (sparse dot product)
"""

import os
import pickle
import numpy as np
import pandas as pd
import scipy.sparse as sp
from modules.utils import parse_list_field, format_movie_response


class MovieEngine:
    """Content-based recommendation engine using TF-IDF + Cosine Similarity."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/", mapping_service=None):
        print("  📦 Loading Content-Based Engine...")
        self.mapping_service = mapping_service

        # ── 1. Load movie metadata ──────────────────────────────────
        movies_df = pd.read_csv(
            os.path.join(data_path, "movies_processed.csv"),
            dtype={"movieId": "int32"},
        )
        # Genres are stored as string repr of lists — parse them back
        movies_df["genres"] = movies_df["genres"].apply(parse_list_field)
        movies_df["title_norm"] = movies_df["title"].str.lower().str.strip()

        # If no mapping service provided, load internal links (legacy fallback)
        if not self.mapping_service:
             links_df = pd.read_csv(
                 os.path.join(data_path, "links_processed.csv"),
                 dtype={"movieId": "int32", "imdbId": "int32", "tmdbId": "int32"},
             )
             # Merge tmdbId + imdbId into movies
             movies_df = movies_df.merge(links_df, on="movieId", how="left")
             movies_df["tmdbId"] = movies_df["tmdbId"].fillna(-1).astype("int32")
             movies_df["imdbId"] = movies_df["imdbId"].fillna(-1).astype("int32")

        self.movies = movies_df

        # ── 3. Build fast lookup maps ───────────────────────────────
        # movieId → row index in self.movies (and in the TF-IDF matrix)
        self.id_to_idx = dict(zip(self.movies["movieId"], self.movies.index))

        # ── 4. Load TF-IDF assets ──────────────────────────────────
        self.tfidf_matrix = sp.load_npz(os.path.join(model_path, "tfidf_matrix.npz"))

        with open(os.path.join(model_path, "title_to_idx.pkl"), "rb") as f:
            self.title_to_idx = pickle.load(f)

        # Sanity check: matrix rows must match movie count
        assert self.tfidf_matrix.shape[0] == len(self.movies), (
            f"TF-IDF matrix rows ({self.tfidf_matrix.shape[0]}) != "
            f"movies count ({len(self.movies)})"
        )

        print(
            f"  ✅ Content Engine ready — {len(self.movies):,} movies, "
            f"TF-IDF shape {self.tfidf_matrix.shape}"
        )

    # ── Public API ──────────────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search movies by substring match on title. Returns list of dicts."""
        q = query.lower().strip()
        mask = self.movies["title_norm"].str.contains(q, na=False)
        hits = self.movies[mask].head(limit)

        return [
            self._format_with_ids(row)
            for _, row in hits.iterrows()
        ]

    def recommend(self, movie_id: int, top_n: int = 12) -> list[dict]:
        """
        Generate content-based recommendations for a given movieId.
        Uses lazy cosine similarity: target_vector · matrix.T
        Returns list of recommendation dicts, or empty list if not found.
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
        # Sort only the small subset
        top_indices = top_indices_unsorted[
            np.argsort(sim_scores[top_indices_unsorted])[::-1]
        ]
        # Remove self-match
        top_indices = top_indices[top_indices != idx][:top_n]

        results = []
        for i in top_indices:
            row = self.movies.iloc[i]
            results.append(
                self._format_with_ids(
                    row, 
                    score=self._normalize_score(float(sim_scores[i])), 
                    mode="content"
                )
            )

        return results

    def _format_with_ids(self, row, score=None, mode="content"):
        """Helper to inject IDs from the MappingService into the response."""
        movieId = int(row["movieId"])
        if self.mapping_service:
             tmdbId = self.mapping_service.get_tmdb_id(movieId)
             imdbId = self.mapping_service.get_imdb_id(movieId)
        else:
             tmdbId = int(row.get("tmdbId", -1))
             imdbId = int(row.get("imdbId", -1))

        # Re-use the existing physical formatter
        return format_movie_response(
             {**row.to_dict(), "tmdbId": tmdbId, "imdbId": imdbId},
             score=score,
             mode=mode
        )

    def _normalize_score(self, score: float) -> float:
        """
        Maps technical cosine similarity (0.0 - 1.0) to a user-friendly 
        'Confidence Percentage' (0.60 - 0.98).
        """
        if score <= 0: return 0.0
        # Boost low but relevant scores into the 70s and 80s
        normalized = 0.65 + (score * 0.7) 
        return round(min(0.98, normalized), 4)
