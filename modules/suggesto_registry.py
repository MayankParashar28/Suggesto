"""
Suggesto Registry
=================
Architecture to support multi-content discovery (Movies, Music, Courses).
"""

class SuggestoRegistry:
    def __init__(self):
        self.engines = {}

    def register(self, name: str, engine):
        """Register a recommendation engine for a specific content type."""
        self.engines[name] = engine
        print(f"  📌 Registered {name.capitalize()} Engine")

    def get_engine(self, name: str):
        """Retrieve the engine for a specific content type."""
        return self.engines.get(name)

    def list_categories(self):
        """List all available discovery categories."""
        return list(self.engines.keys())
