from modules.music_recommender import MusicEngine

class AudioService:
    """
    Audio Domain Service
    ====================
    Wraps the MusicEngine to provide a high-level service interface
    for audio discovery and recommendation.
    """
    def __init__(self, data_path: str = "processed/", model_path: str = "models/"):
        self.engine = MusicEngine(data_path=data_path, model_path=model_path)
        print("  📻 Audio Service initialized")

    def search(self, query: str, limit: int = 12):
        """Perform search across the audio catalog."""
        return self.engine.search(query, limit=limit)

    def recommend(self, item_id: str, top_n: int = 12, genre: str = None):
        """Generate audio recommendations."""
        return self.engine.recommend(item_id, top_n=top_n)

    def discover(self, limit: int = 24, offset: int = 0):
        """Get discovery content for the audio domain."""
        return self.engine.discover(limit=limit, offset=offset)
