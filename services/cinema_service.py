from modules.movie_recommender import MovieEngine
from modules.collab_recommender import CollabEngine
from modules.hybrid_recommender import HybridEngine
from services.mapping import MappingService

class CinemaService:
    """
    Cinema Domain Service
    =====================
    Orchestrates movie discovery by integrating content-based,
    collaborative, and hybrid recommendation strategies.
    """
    def __init__(self, data_path: str = "processed/", model_path: str = "models/"):
        mapping_service = MappingService(data_path=data_path)
        # Content Engine
        self.movie_engine = MovieEngine(data_path=data_path, model_path=model_path, mapping_service=mapping_service)
        # Collaborative Engine
        self.collab_engine = CollabEngine(data_path=data_path, model_path=model_path)
        # Hybrid Interleaving
        self.hybrid_engine = HybridEngine(self.movie_engine, self.collab_engine)
        print("  🎬 Cinema Service initialized")

    def search(self, query: str, limit: int = 12):
        """Search across the MovieLens catalog."""
        return self.movie_engine.search(query, limit=limit)

    def recommend(self, movie_id: int, top_n: int = 12, mode: str = "hybrid", genre: str = None):
        """Generate movie recommendations based on selected mode."""
        if mode == "hybrid":
            return self.hybrid_engine.recommend(movie_id, top_n=top_n, genre=genre)
        elif mode == "collaborative":
            return self.collab_engine.recommend(movie_id, top_n=top_n)
        return self.movie_engine.recommend(movie_id, top_n=top_n)

    def discover(self, limit: int = 24, offset: int = 0):
        """Get discovery content for the cinema domain."""
        return self.movie_engine.discover(limit=limit, offset=offset)
