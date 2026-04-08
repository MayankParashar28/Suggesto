import os
import csv
from typing import Dict, Any, Optional

class MappingService:
    """
    High-performance ID mapping service (Zero-Scipy).
    Supports multiple categories (Movies, Music, Learning) by loading 
    cross-reference CSVs into O(1) memory dictionaries.
    """
    def __init__(self, data_path: str = "processed/"):
        self.data_path = data_path
        
        # Structure: { category: { source_id: { target_key: target_id } } }
        self.store: Dict[str, Dict[int, Dict[str, Any]]] = {
            "movies": {},
            "songs": {}
        }
        
        # Load initial movie mappings
        self._load_category("movies", "links_processed.csv", source_key="movieId")

    def _load_category(self, category: str, filename: str, source_key: str):
        path = os.path.join(self.data_path, filename)
        if not os.path.exists(path):
            return

        print(f"  🔗 Loading {category} mappings from {filename}...")
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        sid = int(row[source_key])
                        # Store all other columns as potential mapping targets
                        self.store[category][sid] = {
                            k: (int(v) if v and str(v) != '-1' and str(v).strip() != "" else -1) 
                            for k, v in row.items() if k != source_key
                        }
                    except (ValueError, KeyError):
                        continue
            print(f"  ✅ {category.capitalize()} mappings ready — {len(self.store[category]):,} IDs.")
        except Exception as e:
            print(f"  ❌ Failed to load {category} mappings: {e}")

    def get_id(self, category: str, source_id: int, target_key: str) -> Any:
        """Generic lookup for any ID cross-reference."""
        category_data = self.store.get(category, {})
        item_data = category_data.get(source_id, {})
        return item_data.get(target_key, -1)

    # Legacy-compatible helpers for the MovieEngine
    def get_tmdb_id(self, movie_id: int) -> int:
        return self.get_id("movies", movie_id, "tmdbId")

    def get_imdb_id(self, movie_id: int) -> int:
        return self.get_id("movies", movie_id, "imdbId")
