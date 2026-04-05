import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

from modules.movie_recommender import MovieEngine
from modules.collab_recommender import CollabEngine
from modules.hybrid_recommender import HybridEngine
from modules.suggesto_registry import SuggestoRegistry
from services.tmdb import TMDBService
from services.mapping import MappingService

# ── Load environment variables ──────────────────────────────────
load_dotenv()

# ── API Models ──────────────────────────────────────────────────
class CacheUpdate(BaseModel):
    tmdbId: int
    data: Dict[str, Any]

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    mode: Optional[str] = None
    genre: Optional[str] = None
    category: Optional[str] = None

# ── Application Factory ──────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Suggesto Discovery API",
        version="2.0.0",
        description="Hybrid Recommendation Engine for Movies, Songs, and Courses."
    )

    # 1. Initialize Services and Engines
    print("🚀 Initializing Suggesto Hub (Fast Mapping Edition)...")
    registry = SuggestoRegistry()
    
    # Paths (Could be moved to a config.py)
    DATA_PATH = "processed/"
    MODEL_PATH = "models/"

    # New High-Performance ID Mapper
    mapping_service = MappingService(data_path=DATA_PATH)

    movie_engine = MovieEngine(data_path=DATA_PATH, model_path=MODEL_PATH, mapping_service=mapping_service)

    collab_engine = CollabEngine(data_path=DATA_PATH, model_path=MODEL_PATH)
    hybrid_engine = HybridEngine(movie_engine, collab_engine)

    registry.register("movies", hybrid_engine)
    # Future category placeholders
    registry.register("songs", None)
    registry.register("courses", None)

    # 2. TMDB Service (Caching & Proxy)
    tmdb_service = TMDBService()

    # 3. Warm the cache in the background for a few movies to make it "instant"
    @app.on_event("startup")
    async def warmup_cache():
        print("🔥 Warming TMDB Cache...")
        # Just grab some movies from the engine to pre-populate metadata
        # (Practical heuristic: search for 'a' to get 10-20 varied popular titles)
        try:
             sample_movies = movie_engine.search("a", limit=24)
             for movie in sample_movies:
                 tid = movie.get("tmdbId")
                 if tid and tid > 0:
                     # Check if hit/cache
                     await tmdb_service.get_movie_details(tid)
             print(f"✅ Cache warmed with {len(sample_movies)} titles.")
        except Exception as e:
             print(f"⚠️ Cache warmup skipped: {e}")

    # 4. Mount Static Files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # ── Routes ──────────────────────────────────────────────────

    @app.get("/", include_in_schema=False)
    async def read_root():
        """Redirect root to the frontend dashboard."""
        return RedirectResponse(url="/static/index.html")

    @app.get("/api/v1/tmdb/movie/{tmdb_id}")
    async def get_tmdb_movie(tmdb_id: int):
        """Proxy request to TMDB to hide API key and cache metadata."""
        return await tmdb_service.get_movie_details(tmdb_id)

    @app.get("/api/v1/movies/search")
    async def search_movies(q: str = Query(..., min_length=2)):
        """Search for movies with metadata enrichment."""
        results = movie_engine.search(q, limit=12)
        return {"results": tmdb_service.enrich_recommendations(results)}

    @app.get("/api/v1/movies/recommend/{movie_id}")
    async def recommend_movies(
        movie_id: int, 
        mode: str = Query("hybrid", pattern="^(content|collaborative|hybrid)$"), 
        genre: Optional[str] = None
    ):
        """Generate recommendations for a specific movieId."""
        if mode == "hybrid":
            recs = hybrid_engine.recommend(movie_id, top_n=12, genre=genre)
        elif mode == "collaborative":
            recs = collab_engine.recommend(movie_id, top_n=12)
        else:
            recs = movie_engine.recommend(movie_id, top_n=12)
        
        # Fallback cascade logic
        if not recs:
            recs = movie_engine.recommend(movie_id, top_n=12)
            
        if not recs:
             raise HTTPException(status_code=404, detail="No recommendations found.")

        enriched = tmdb_service.enrich_recommendations(recs)
        return {"recommendations": enriched, "mode": mode, "genre": genre}

    @app.get("/api/v1/recommend/{content_type}/{item_id}")
    async def universal_recommend(
        content_type: str, 
        item_id: int, 
        limit: int = 12, 
        genre: Optional[str] = None
    ):
        """Unified endpoint for Movies, Songs, Courses, etc."""
        engine = registry.get_engine(content_type)
        if not engine:
            raise HTTPException(status_code=404, detail=f"Category '{content_type}' is not active.")
        
        if engine is None: # Placeholder case
            return {"recommendations": [], "status": "coming_soon"}

        recs = engine.recommend(item_id, top_n=limit, genre=genre)
        if not recs:
            raise HTTPException(status_code=404, detail="Item not found.")

        enriched = tmdb_service.enrich_recommendations(recs)
        return {"recommendations": enriched, "category": content_type}

    @app.post("/api/v1/metadata/cache", include_in_schema=False)
    async def update_metadata_cache(payload: CacheUpdate):
        tmdb_service.update_cache(payload.tmdbId, payload.data)
        return {"status": "Cached"}

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
