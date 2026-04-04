"""
Hybrid Recommendation Engine
=============================
Blends content-based and collaborative results.
Falls back to content-only when collaborative is unavailable.
"""


class HybridEngine:
    """Blends content + collaborative recommendations."""

    def __init__(self, movie_engine, collab_engine):
        self.content = movie_engine
        self.collab = collab_engine
        print("  🔀 Hybrid Engine ready")

    def recommend(self, movie_id: int, top_n: int = 12, genre: str = None) -> list[dict]:
        """
        Generate hybrid recommendations.
        Falls back to content-only when collaborative returns nothing.
        Optionally filters by genre.
        """
        # Get content-based results
        content_recs = self.content.recommend(movie_id, top_n=top_n * 2)

        # Get collaborative results
        collab_recs = self.collab.recommend(movie_id, top_n=top_n * 2)

        if collab_recs:
            # Blend: interleave collab and content, deduplicating by movieId
            seen = set()
            blended = []
            # Alternate: collab, content, collab, content...
            max_len = max(len(collab_recs), len(content_recs))
            for i in range(max_len):
                if i < len(collab_recs):
                    mid = collab_recs[i]["movieId"]
                    if mid not in seen:
                        seen.add(mid)
                        blended.append(collab_recs[i])
                if i < len(content_recs):
                    mid = content_recs[i]["movieId"]
                    if mid not in seen:
                        seen.add(mid)
                        blended.append(content_recs[i])
        else:
            # Fallback: content-only
            blended = content_recs

        # Genre filter (if requested)
        if genre:
            genre_lower = genre.lower()
            blended = [
                r for r in blended
                if any(g.lower() == genre_lower for g in r.get("genres", []))
            ]

        # Tag each result with hybrid mode
        for r in blended:
            r["mode"] = "hybrid"

        return blended[:top_n]
