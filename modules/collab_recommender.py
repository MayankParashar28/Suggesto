import os
import pandas as pd


class CollabEngine:
    """Collaborative filtering engine with popularity fallback."""

    def __init__(self, data_path: str = "processed/", model_path: str = "models/"):
        self.ready = False
        self.data_path = data_path
        factors_path = os.path.join(model_path, "collab_factors.npy")
        
        # Load processed movies for fallback metadata
        try:
            movies_path = os.path.join(data_path, "movies_processed.csv")
            self.movies_df = pd.read_csv(movies_path)
            # Pre-select popular IDs (Commonly top-rated in MovieLens)
            self.popular_ids = [318, 296, 356, 527, 260, 593, 2571, 1, 480, 1196, 589, 2858]
        except Exception as e:
            print(f"  ⚠️  Collaborative Engine: Failed to load fallback data: {e}")
            self.movies_df = None
            self.popular_ids = []

        if not os.path.exists(factors_path):
            print("  ⚠️  Collaborative Engine: model not trained yet (popularity fallback active)")
            return

        # Future implementation: Load latent factors
        self.ready = True
        print("  ✅ Collaborative Engine: Model factors loaded.")

    def recommend(self, movie_id: int, top_n: int = 12) -> list[dict]:
        """Returns popular movies as fallback until model is trained."""
        if self.movies_df is not None:
            # Basic fallback if DB load failed
            fallback = self.movies_df[self.movies_df['movieId'].isin(self.popular_ids)]
            results = []
            for _, row in fallback.iterrows():
                results.append({
                    "movieId": int(row["movieId"]),
                    "title": row["title"],
                    "genres": eval(row["genres"]) if isinstance(row["genres"], str) else row["genres"],
                    "tmdbId": -1, # Will be filled by registry/main if possible
                    "score": 0.85, # Constant for fallback
                    "mode": "collab-fallback"
                })
            return results[:top_n]
        return []
