"""
Content-Based Movie Recommendation Engine (Zero-Scipy Edition)
============================================================
Loads pre-trained TF-IDF assets and serves recommendations via
a manual sparse dot-product implementation in Pure Numpy.

Optimization: 
  - Removes 'scipy' dependency (~150MB).
  - Uses native 'numpy' with manual CSR matrix math.
"""

import os
import csv
import pickle
import re
import numpy as np
from sys import intern
from modules.utils import parse_list_field, format_movie_response


class MovieEngine:
    """Content-based recommendation engine (Zero-Scipy)."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/", mapping_service=None):
        print("  📦 Loading Content-Based Engine (Pandas Optimization)...")
        self.mapping_service = mapping_service

        # ── 1. Load movie metadata via Pandas ───────────────────────
        import pandas as pd
        movies_file = os.path.join(data_path, "movies_processed.csv")
        self.df = pd.read_csv(movies_file)
        self.df["title_norm"] = self.df["title"].str.lower().str.strip()
        self.df["_idx"] = np.arange(len(self.df))
        
        # ID lookup map for O(1) performance
        self.id_to_idx = dict(zip(self.df["movieId"], self.df["_idx"]))

        # Pre-calculate discovery pool (movies with valid posters/IDs)
        if self.mapping_service:
            v_tmdb = pd.to_numeric(self.df["movieId"].apply(self.mapping_service.get_tmdb_id), errors='coerce').fillna(-1)
            self.discover_pool = self.df[v_tmdb > 0].index.tolist()
        else:
            self.discover_pool = self.df[self.df["tmdbId"] > 0].index.tolist() if "tmdbId" in self.df.columns else self.df.index.tolist()


        # ── 2. Load Numpy-only CSR Components ───────────────────────
        self.data = np.load(os.path.join(model_path, "tfidf_data.npy"))
        self.indices = np.load(os.path.join(model_path, "tfidf_indices.npy"))
        self.indptr = np.load(os.path.join(model_path, "tfidf_indptr.npy"))

        with open(os.path.join(model_path, "tfidf_shape.txt"), "r") as f:
            shape = f.read().split(",")
            self.num_rows = int(shape[0])
            self.num_cols = int(shape[1])

        # Sanity check
        assert self.num_rows == len(self.df), (
            f"Numpy matrix rows ({self.num_rows}) != "
            f"movies count ({len(self.df)})"
        )

        # ── 3. Pre-build row_map for vectorized dot products ────────
        # Maps each non-zero element index -> its row number
        # Enables O(nnz) sparse dot products via np.bincount
        self.row_map = np.zeros(len(self.indices), dtype=np.int32)
        for r in range(self.num_rows):
            s, e = self.indptr[r], self.indptr[r+1]
            self.row_map[s:e] = r

        print(f"  ✅ Content Engine ready — {len(self.df):,} movies (Pandas Vectorized).")

        # ── 4. Pre-calculate Fuzzy search pool (O4) ────────────────
        # Clean titles (remove year) for the fuzzy matching keys, 
        # but map them back to original titles for the suggestion.
        self._fuzzy_map = {
            re.sub(r"\s+\(\d{4}\)$", "", str(title)): title 
            for title in self.df["title"].iloc[:40000] # Top 40k for performance vs accuracy
        }
        self._fuzzy_choices = list(self._fuzzy_map.keys())

    # ── Public API ──────────────────────────────────────────────────

    def search(self, query: str, limit: int = 15) -> tuple[list[dict], str | None]:
        """Vectorized search movies by title with fuzzy fallback."""
        from modules.utils import get_fuzzy_suggestion
        q = query.lower().strip()
        mask = self.df["title_norm"].str.contains(q, na=False, regex=False)
        hits = self.df[mask].head(limit)
        results = [self._format_with_ids(row.to_dict()) for _, row in hits.iterrows()]
        
        suggestion = None
        if not results:
            # Only try fuzzy matching if direct search yields nothing
            match = get_fuzzy_suggestion(query, self._fuzzy_choices, threshold=0.5)
            if match:
                suggestion = self._fuzzy_map.get(match)
            
        return results, suggestion

    def recommend(self, movie_id: int, top_n: int = 12) -> list[dict]:
        """
        Vectorized content-based recommendations via row_map + bincount.
        O(nnz) sparse dot product — ~50ms for 87K movies.
        """
        idx = self.id_to_idx.get(movie_id)
        if idx is None: return []

        # 1. Get non-zeros of the query row
        start, end = self.indptr[idx], self.indptr[idx+1]
        if start == end: return []
        row_indices = self.indices[start:end]
        row_data = self.data[start:end]

        # 2. Build query lookup
        query_map = dict(zip(row_indices.tolist(), row_data.tolist()))

        # 3. Vectorized Sparse Dot Product via row_map + bincount
        # Find all matrix entries sharing columns with query row
        mask = np.isin(self.indices, row_indices)
        if not np.any(mask): return []

        matching_vals = self.data[mask]
        matching_rows = self.row_map[mask]
        matching_cols = self.indices[mask]

        # Weight each match by the query vector's value for that column
        weights = np.array([query_map[c] for c in matching_cols.tolist()])
        contributions = matching_vals * weights

        # Sum contributions per row
        scores = np.bincount(matching_rows, weights=contributions, minlength=self.num_rows)

        # 4. Fast top-N via argpartition
        n_candidates = min(top_n + 1, len(scores))
        top_indices_unsorted = np.argpartition(scores, -n_candidates)[-n_candidates:]
        top_indices = top_indices_unsorted[np.argsort(scores[top_indices_unsorted])[::-1]]
        top_indices = top_indices[top_indices != idx][:top_n]

        results = []
        for i in top_indices:
            row = self.df.iloc[i].to_dict()
            results.append(
                self._format_with_ids(
                    row, 
                    score=self._normalize_score(float(scores[i])), 
                    mode="content"
                )
            )
        return results

    def _format_with_ids(self, movie, score=None, mode="content"):
        movieId = movie["movieId"]
        if self.mapping_service:
             tmdbId = self.mapping_service.get_tmdb_id(movieId)
             imdbId = self.mapping_service.get_imdb_id(movieId)
        else:
             tmdbId = int(movie.get("tmdbId", -1))
             imdbId = int(movie.get("imdbId", -1))
        return format_movie_response(
             {**movie, "tmdbId": tmdbId, "imdbId": imdbId},
             score=score,
             mode=mode
        )

    def discover(self, limit: int = 24, offset: int = 0) -> list[dict]:
        """Return a deterministic selection of movies for pagination support."""
        start = offset
        end = offset + limit
        # Slice from the discover pool (already sorted by popularity)
        sample_indices = self.discover_pool[start:end]
        rows = self.df.iloc[sample_indices]
        return [self._format_with_ids(row.to_dict()) for _, row in rows.iterrows()]

    def _normalize_score(self, score: float) -> float:
        if score <= 0: return 0.0
        normalized = 0.65 + (score * 0.7) 
        return round(min(0.98, normalized), 4)
