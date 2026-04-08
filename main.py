import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
from dotenv import load_dotenv

from modules.movie_recommender import MovieEngine
from modules.music_recommender import MusicEngine
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

# ── Application Factory ──────────────────────────────────────────

# 1. Initialize Services and Engines (Parallel Startup)
print("🚀 Initializing Suggesto Hub (High-Speed Parallel Edition)...")
registry = SuggestoRegistry()

DATA_PATH = "processed/"
MODEL_PATH = "models/"

mapping_service = MappingService(data_path=DATA_PATH)
tmdb_service = TMDBService()

def load_engines():
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_movie = executor.submit(MovieEngine, data_path=DATA_PATH, model_path=MODEL_PATH, mapping_service=mapping_service)
        f_music = executor.submit(MusicEngine, data_path=DATA_PATH, model_path=MODEL_PATH)
        f_collab = executor.submit(CollabEngine, data_path=DATA_PATH, model_path=MODEL_PATH)
        
        return f_movie.result(), f_music.result(), f_collab.result()

movie_engine, music_engine, collab_engine = load_engines()
hybrid_engine = HybridEngine(movie_engine, collab_engine)

registry.register("movies", hybrid_engine)
registry.register("songs", music_engine)

tmdb_service = TMDBService()

# 2. Lifespan for Startup/Shutdown (Modern FastAPI Pattern)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔥 Warming TMDB Cache...")
    try:
         sample_movies = movie_engine.search("a", limit=24)
         for movie in sample_movies:
             tid = movie.get("tmdbId")
             if tid and tid > 0:
                 await tmdb_service.get_movie_details(tid)
         print(f"✅ Cache warmed with {len(sample_movies)} titles.")
    except Exception as e:
         print(f"⚠️ Cache warmup skipped: {e}")
    yield

# 3. App Instance
app = FastAPI(
    title="Suggesto Discovery API",
    version="2.1.0",
    description="Hybrid Recommendation Engine for Movies and Songs.",
    lifespan=lifespan
)

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
    # Batch-fetch TMDB metadata for all results concurrently
    tmdb_ids = [r["tmdbId"] for r in results if r.get("tmdbId", -1) > 0]
    if tmdb_ids:
        batch_data = await tmdb_service.batch_get_movie_details(tmdb_ids)
        for r in results:
            tid = str(r.get("tmdbId"))
            if tid in batch_data:
                r["cached"] = batch_data[tid]
    return {"results": results}

@app.get("/api/v1/songs/search")
async def search_songs(q: str = Query(..., min_length=2)):
    """Search for songs via the Zero-Scipy MusicEngine."""
    if music_engine is None:
        return {"results": [], "status": "Music engine not available — model files missing."}
    results = music_engine.search(q, limit=24)
    return {"results": results}

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

    # Batch-fetch TMDB metadata concurrently
    tmdb_ids = [r["tmdbId"] for r in recs if r.get("tmdbId", -1) > 0]
    if tmdb_ids:
        batch_data = await tmdb_service.batch_get_movie_details(tmdb_ids)
        for r in recs:
            tid = str(r.get("tmdbId"))
            if tid in batch_data:
                r["cached"] = batch_data[tid]
    return {"recommendations": recs, "mode": mode, "genre": genre}

@app.get("/api/v1/recommend/{content_type}/{item_id}")
async def universal_recommend(
    content_type: str, 
    item_id: str, 
    limit: int = 12, 
    genre: Optional[str] = None
):
    """Unified endpoint for Movies, Songs, Courses, etc."""
    engine = registry.get_engine(content_type)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Category '{content_type}' is not active.")
    
    if engine is None: # Placeholder case
        return {"recommendations": [], "status": "coming_soon"}

    # Normalize item_id type (movies expect int, songs expect str)
    try:
        if content_type == "movies":
            item_id = int(item_id)
    except ValueError:
         raise HTTPException(status_code=400, detail=f"Numeric ID required for {content_type}")

    recs = engine.recommend(item_id, top_n=limit, genre=genre)
    if not recs:
        raise HTTPException(status_code=404, detail="Item not found.")

    # Only enrich with TMDB if it's a movie
    if content_type == "movies":
        enriched = tmdb_service.enrich_recommendations(recs)
    else:
        enriched = recs # Return as is for songs
    
    return {"recommendations": enriched, "category": content_type}

@app.get("/api/v1/discover/{content_type}")
async def discover_content(content_type: str, limit: int = 24):
    """Serve a random selection of content for the home page."""
    engine = registry.get_engine(content_type)
    if not engine:
         raise HTTPException(status_code=404, detail=f"Category '{content_type}' is not active.")
    
    results = engine.discover(limit=limit)
    
    # Enrichment for movies
    if content_type == "movies":
        tmdb_ids = [r["tmdbId"] for r in results if r.get("tmdbId", -1) > 0]
        if tmdb_ids:
            batch_data = await tmdb_service.batch_get_movie_details(tmdb_ids)
            for r in results:
                tid = str(r.get("tmdbId"))
                if tid in batch_data:
                    r["cached"] = batch_data[tid]
    
    return {"results": results}

@app.post("/api/v1/tmdb/batch")
async def batch_tmdb(payload: dict):
    """Batch fetch TMDB details for multiple movies at once."""
    ids = payload.get("ids", [])
    if not ids or len(ids) > 50:
        return {"results": {}}
    results = await tmdb_service.batch_get_movie_details(ids)
    return {"results": results}

@app.post("/api/v1/metadata/cache", include_in_schema=False)
async def update_metadata_cache(payload: CacheUpdate):
    tmdb_service.update_cache(payload.tmdbId, payload.data)
    return {"status": "Cached"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
