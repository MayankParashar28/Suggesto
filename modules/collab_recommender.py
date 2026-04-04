"""
Collaborative Filtering Engine — Stub
======================================
Placeholder until the collaborative model is trained.
Returns empty recommendations so the server can start gracefully.
"""

import os


class CollabEngine:
    """Collaborative filtering engine (stub — not yet trained)."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/"):
        self.ready = False
        factors_path = os.path.join(model_path, "collab_factors.npy")

        if not os.path.exists(factors_path):
            print("  ⚠️  Collaborative Engine: model not trained yet (stub active)")
            return

        # Will be implemented after training
        print("  ⚠️  Collaborative Engine: stub active")

    def recommend(self, movie_id: int, top_n: int = 12) -> list[dict]:
        """Returns empty list until the model is trained."""
        return []
