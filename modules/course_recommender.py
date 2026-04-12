import os
import pandas as pd
import numpy as np
from modules.utils import format_movie_response # We'll adapt this

class CourseEngine:
    """The 'Learning Scribbles' discovery engine."""

    def __init__(self, data_path: str = "processed/"):
        print("  📚 Loading Learning Scribbles (Multi-Platform Merge)...")
        
        udemy_file = os.path.join(data_path, "courses_processed.csv")
        youtube_file = os.path.join(data_path, "youtube_courses.csv")
        
        dfs = []
        if os.path.exists(udemy_file):
            dfs.append(pd.read_csv(udemy_file))
        if os.path.exists(youtube_file):
            dfs.append(pd.read_csv(youtube_file))

        if dfs:
            self.df = pd.concat(dfs, ignore_index=True)
            self.df["title_norm"] = self.df["title"].str.lower().str.strip()
            self.df["instructor_norm"] = self.df["instructor"].str.lower().str.strip()
            self.df["platform_norm"] = self.df["platform"].str.lower().str.strip()
            
            # Create a searchable content field (title + platform + category)
            self.df["search_content"] = (
                self.df["title_norm"].fillna("") + " " + 
                self.df["platform_norm"].fillna("") + " " + 
                self.df["category"].str.lower().fillna("")
            )
            
            self.df["_idx"] = np.arange(len(self.df))
            self.id_to_idx = dict(zip(self.df["courseId"], self.df["_idx"]))
        
            # O4: Pre-compute fuzzy search pool
            self._fuzzy_choices = (
                self.df["title"].tolist() + 
                self.df["instructor"].unique().tolist()
            )
        else:
            print(f"  ❌ No course metadata found.")
            self.df = pd.DataFrame()
            self.id_to_idx = {}
            self._fuzzy_choices = []

        print(f"  ✅ Learning Engine ready — {len(self.df):,} courses (Udemy + YouTube).")

    def search(self, query: str, limit: int = 15) -> tuple[list[dict], str | None]:
        """Vectorized search for courses with fuzzy fallback."""
        from modules.utils import get_fuzzy_suggestion
        if self.df.empty: return [], None
        q = query.lower().strip()
        mask = (
            self.df["title_norm"].str.contains(q, na=False, regex=False) | 
            self.df["instructor_norm"].str.contains(q, na=False, regex=False) |
            self.df["platform_norm"].str.contains(q, na=False, regex=False)
        )
        hits = self.df[mask].head(limit)
        results = [self._format_response(row.to_dict()) for _, row in hits.iterrows()]
        
        suggestion = None
        if not results:
            suggestion = get_fuzzy_suggestion(query, self._fuzzy_choices)
            
        return results, suggestion

    def recommend(self, course_id: int, top_n: int = 12, genre: str = None) -> list[dict]:
        """Keyword-based recommendations within same category or related topics."""
        if self.df.empty: return []
        idx = self.id_to_idx.get(course_id)
        if idx is None: return []
        
        target_row = self.df.iloc[idx]
        target_title_words = set(target_row["title_norm"].split())
        
        # 1. Filter by same category or platform (or specific genre if provided)
        if genre:
            mask = (self.df["category"].str.lower() == genre.lower())
        else:
            mask = (self.df["category"] == target_row["category"]) | (self.df["platform"] == target_row["platform"])
        
        candidates = self.df[mask & (self.df["courseId"] != course_id)].copy()
        
        if candidates.empty:
            return self.discover(limit=top_n)

        # 2. Simple Keyword Overlap Score
        def get_overlap(title):
            words = set(str(title).lower().split())
            return len(target_title_words.intersection(words))

        candidates["overlap"] = candidates["title"].apply(get_overlap)
        
        # Sort by overlap score and then rating
        results = candidates.sort_values(by=["overlap", "rating"], ascending=False).head(top_n)
        
        return [self._format_response(row.to_dict()) for _, row in results.iterrows()]

    def discover(self, limit: int = 24, offset: int = 0) -> list[dict]:
        """Return a selection of courses with pagination support."""
        if self.df.empty: return []
        start = offset
        end = offset + limit
        rows = self.df.iloc[start:end]
        return [self._format_response(row.to_dict()) for _, row in rows.iterrows()]

    def _format_response(self, course: dict) -> dict:
        """Map course metadata to Suggesto's card format."""
        return {
            "movieId": course["courseId"], # Mapping to common ID field
            "title": course["title"],
            "artist": course["instructor"], # Using artist field for instructor
            "album": course["platform"], # Using album field for platform
            "releaseYear": course["category"], # Using releaseYear for Category pill
            "rating": course["rating"],
            "tmdbId": -2, # Special ID for Kurses
            "url": course["url"],
            "category": course["category"]
        }
