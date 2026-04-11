import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
from dotenv import load_dotenv

from modules.movie_recommender import MovieEngine
from modules.music_recommender import MusicEngine
from modules.course_recommender import CourseEngine
from modules.collab_recommender import CollabEngine
from modules.hybrid_recommender import HybridEngine
from modules.inkpick_registry import InkpickRegistry
from modules.utils import parse_list_field, format_movie_response, sanitize_query
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
registry = InkpickRegistry()

DATA_PATH = "processed/"
MODEL_PATH = "models/"

mapping_service = MappingService(data_path=DATA_PATH)
tmdb_service = TMDBService()

def load_engines(data_path: str, model_path: str):
    import concurrent.futures
    # O3: Only load CollabEngine if model exists
    collab_model_path = os.path.join(model_path, "collab_factors.npy")
    mapping_service = MappingService(data_path=data_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_movie = executor.submit(MovieEngine, data_path=data_path, model_path=model_path, mapping_service=mapping_service)
        f_music = executor.submit(MusicEngine, data_path=data_path, model_path=model_path)
        f_course = executor.submit(CourseEngine, data_path=data_path)
        f_collab = executor.submit(CollabEngine, data_path=data_path, model_path=model_path) if os.path.exists(collab_model_path) else None
        
        movie = f_movie.result()
        music = f_music.result()
        course = f_course.result()
        collab = f_collab.result() if f_collab else CollabEngine(data_path=data_path, model_path=model_path)
        
        return movie, music, course, collab

# 2. Lifespan for Startup/Shutdown (Modern FastAPI Pattern)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Initializing Inkpick Engines (Lifespan Mode)...")
    DATA_PATH = "processed/"
    MODEL_PATH = "models/"
    
    # Load engines in parallel without blocking main loop
    movie, music, course, collab = load_engines(DATA_PATH, MODEL_PATH)
    hybrid = HybridEngine(movie, collab)
    
    # Store in app state
    app.state.movie_engine = movie
    app.state.music_engine = music
    app.state.course_engine = course
    # Store in app state
    app.state.movie_engine = movie
    app.state.music_engine = music
    app.state.course_engine = course
    app.state.collab_engine = collab
    app.state.hybrid_engine = hybrid
    
    # Register in global registry
    registry.register("movies", hybrid)
    registry.register("songs", music)
    registry.register("courses", course)
    
    # Verify Configuration
    if not tmdb_service.api_key:
         print("  ⚠️  CRITICAL: TMDB_API_KEY is missing! Discovery metadata will be limited to stubs.")
    
    # Optimized Warmup for Vercel (Cold Start Prevention)
    is_vercel = os.getenv("VERCEL") == "1"
    warmup_count = 6 if is_vercel else 12
    
    print(f"🔥 Warming TMDB Cache ({warmup_count} titles)...")
    try:
         results, _ = movie.search("a", limit=warmup_count)
         for m in results:
             tid = m.get("tmdbId")
             if tid and tid > 0:
                 await tmdb_service.get_movie_details(tid)
         print(f"✅ Cache warmed successfully.")
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
    """Search for movies via the Zero-Numpy MovieEngine."""
    q = sanitize_query(q)
    if len(q) < 2:
        return {"results": [], "suggestion": None}

    movie_engine = app.state.movie_engine
    results, suggestion = movie_engine.search(q, limit=24)
    # Batch-fetch TMDB metadata for all results concurrently
    tmdb_ids = [r["tmdbId"] for r in results if r.get("tmdbId", -1) > 0]
    if tmdb_ids:
        batch_data = await tmdb_service.batch_get_movie_details(tmdb_ids)
        for r in results:
            tid = str(r.get("tmdbId"))
            if tid in batch_data:
                r["cached"] = batch_data[tid]
    return {"results": results, "suggestion": suggestion}

@app.get("/api/v1/songs/search")
async def search_songs(q: str = Query(..., min_length=2)):
    """Search for songs via the Zero-Scipy MusicEngine."""
    q = sanitize_query(q)
    if len(q) < 2:
        return {"results": [], "suggestion": None, "status": "Search query too short after cleaning."}

    music_engine = app.state.music_engine
    if music_engine is None:
        return {"results": [], "suggestion": None, "status": "Music engine not available."}
    results, suggestion = music_engine.search(q, limit=24)
    return {"results": results, "suggestion": suggestion}

@app.get("/api/v1/courses/search")
async def search_courses(q: str = Query(..., min_length=2)):
    """Search for courses via the CourseEngine."""
    q = sanitize_query(q)
    if len(q) < 2:
        return {"results": [], "suggestion": None}

    course_engine = app.state.course_engine
    if course_engine is None:
        return {"results": [], "suggestion": None}
    results, suggestion = course_engine.search(q, limit=24)
    return {"results": results, "suggestion": suggestion}

@app.get("/api/v1/movies/recommend/{movie_id}")
async def recommend_movies(
    movie_id: int, 
    mode: str = Query("hybrid", pattern="^(content|collaborative|hybrid)$"), 
    genre: Optional[str] = None
):
    """Generate recommendations for a specific movieId."""
    movie_engine = app.state.movie_engine
    collab_engine = app.state.collab_engine
    hybrid_engine = app.state.hybrid_engine

    if mode == "hybrid":
        recs = hybrid_engine.recommend(movie_id, top_n=12, genre=genre)
    elif mode == "collaborative":
        recs = collab_engine.recommend(movie_id, top_n=12)
    else:
        recs = movie_engine.recommend(movie_id, top_n=12)
    
    # Fallback cascade logic
    if not recs:
        recs = app.state.movie_engine.recommend(movie_id, top_n=12)
        
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
async def update_metadata_cache(
    payload: CacheUpdate, 
    request: Request,
    x_internal_secret: Optional[str] = Header(None)
):
    """Internal endpoint to update metadata cache. Protected by secret token."""
    secret = os.getenv("INTERNAL_SECRET_TOKEN")
    if not secret or x_internal_secret != secret:
        raise HTTPException(status_code=403, detail="Unauthorized internal request.")
        
    tmdb_service.update_cache(payload.tmdbId, payload.data)
    return {"status": "Cached"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
