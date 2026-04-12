from modules.course_recommender import CourseEngine

class EduService:
    """
    Education Domain Service
    ========================
    Wraps the CourseEngine to provide academic content discovery
    for the Udemy catalog.
    """
    def __init__(self, data_path: str = "processed/"):
        self.engine = CourseEngine(data_path=data_path)
        print("  🎓 Education Service initialized")

    def search(self, query: str, limit: int = 12):
        """Perform search across educational courses."""
        return self.engine.search(query, limit=limit)

    def recommend(self, item_id: str, top_n: int = 12, genre: str = None):
        """Generate course recommendations."""
        return self.engine.recommend(item_id, top_n=top_n)

    def discover(self, limit: int = 24, offset: int = 0):
        """Get discovery content for the education domain."""
        return self.engine.discover(limit=limit, offset=offset)
