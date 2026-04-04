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
import ast
import pickle
import numpy as np
import pandas as pd
import scipy.sparse as sp


class MovieEngine:
    """Content-based recommendation engine using TF-IDF + Cosine Similarity."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/"):
        print("  📦 Loading Content-Based Engine...")

        # ── 1. Load movie metadata ──────────────────────────────────
        movies_df = pd.read_csv(
            os.path.join(data_path, "movies_processed.csv"),
            dtype={"movieId": "int32"},
        )
        # Genres are stored as string repr of lists — parse them back
        movies_df["genres"] = movies_df["genres"].apply(self._parse_list_field)
        movies_df["title_norm"] = movies_df["title"].str.lower().str.strip()

        # ── 2. Load links (movieId → tmdbId / imdbId) ──────────────
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
            {
                "movieId": int(row["movieId"]),
                "title": row["title"],
                "genres": row["genres"],
                "releaseYear": (
                    int(row["release_year"])
                    if pd.notna(row["release_year"])
                    else None
                ),
                "tmdbId": int(row["tmdbId"]),
                "imdbId": int(row["imdbId"]),
            }
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

        # ── Build result dicts ──────────────────────────────────────
        results = []
        for i in top_indices:
            row = self.movies.iloc[i]
            results.append(
                {
                    "movieId": int(row["movieId"]),
                    "title": row["title"],
                    "genres": row["genres"],
                    "releaseYear": (
                        int(row["release_year"])
                        if pd.notna(row["release_year"])
                        else None
                    ),
                    "tmdbId": int(row["tmdbId"]),
                    "imdbId": int(row["imdbId"]),
                    "similarity": round(float(sim_scores[i]), 4),
                    "mode": "content",
                }
            )

        return results

    # ── Internal helpers ────────────────────────────────────────────

    @staticmethod
    def _parse_list_field(val):
        """Safely parse stringified Python lists from CSV back to real lists."""
        if isinstance(val, list):
            return val
        if not isinstance(val, str) or val in ("[]", "(no genres listed)"):
            return []
        try:
            parsed = ast.literal_eval(val)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, SyntaxError):
            return [g.strip() for g in val.split("|") if g.strip()]
