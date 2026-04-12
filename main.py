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
from services.cinema_service import CinemaService
from services.audio_service import AudioService
from services.edu_service import EduService

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

def load_services(data_path: str, model_path: str):
    """Load and initialize domain services in parallel."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_cinema = executor.submit(CinemaService, data_path=data_path, model_path=model_path)
        f_audio = executor.submit(AudioService, data_path=data_path, model_path=model_path)
        f_edu = executor.submit(EduService, data_path=data_path)
        
        return f_cinema.result(), f_audio.result(), f_edu.result()

# 2. Lifespan for Startup/Shutdown (Modern FastAPI Pattern)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Initializing Inkpick Engines (Lifespan Mode)...")
    DATA_PATH = "processed/"
    MODEL_PATH = "models/"
    
    # Load services in parallel
    cinema, audio, edu = load_services(DATA_PATH, MODEL_PATH)
    
    # Store in app state
    app.state.cinema_service = cinema
    app.state.audio_service = audio
    app.state.edu_service = edu
    
    # Register in global registry for unified routing
    registry.register("movies", cinema)
    registry.register("songs", audio)
    registry.register("courses", edu)
    
    # Verify Configuration
    if not tmdb_service.api_key:
         print("  ⚠️  CRITICAL: TMDB_API_KEY is missing! Discovery metadata will be limited to stubs.")
    
    # Optimized Warmup for Vercel (Cold Start Prevention)
    is_vercel = os.getenv("VERCEL") == "1"
    warmup_count = 6 if is_vercel else 12
    
    print(f"🔥 Warming TMDB Cache ({warmup_count} titles)...")
    try:
         results, _ = cinema.search("a", limit=warmup_count)
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

@app.get("/api/v1/search/{domain}")
async def universal_search(domain: str, q: str = Query(..., min_length=2), limit: int = 24):
    """Unified search endpoint as specified in README."""
    engine = registry.get_engine(domain)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Category '{domain}' is not active.")
    
    q = sanitize_query(q)
    if len(q) < 2:
        return {"results": [], "suggestion": None}

    results, suggestion = engine.search(q, limit=limit)
    
    # Enrichment for movies
    if domain == "movies":
        tmdb_ids = [r["tmdbId"] for r in results if r.get("tmdbId", -1) > 0]
        if tmdb_ids:
            batch_data = await tmdb_service.batch_get_movie_details(tmdb_ids)
            for r in results:
                tid = str(r.get("tmdbId"))
                if tid in batch_data:
                    r["cached"] = batch_data[tid]
    
    return {"results": results, "suggestion": suggestion}

@app.get("/api/v1/movies/search")
async def search_movies(q: str = Query(..., min_length=2)):
    """Legacy endpoint — redirects to universal search."""
    return await universal_search("movies", q)

@app.get("/api/v1/songs/search")
async def search_songs(q: str = Query(..., min_length=2)):
    """Legacy endpoint — redirects to universal search."""
    return await universal_search("songs", q)

@app.get("/api/v1/courses/search")
async def search_courses(q: str = Query(..., min_length=2)):
    """Legacy endpoint — redirects to universal search."""
    return await universal_search("courses", q)

@app.get("/api/v1/movies/recommend/{movie_id}")
async def recommend_movies(
    movie_id: int, 
    mode: str = Query("hybrid", pattern="^(content|collaborative|hybrid)$"), 
    genre: Optional[str] = None
):
    """Generate recommendations for a specific movieId."""
    cinema = app.state.cinema_service

    if mode == "hybrid":
        recs = cinema.recommend(movie_id, top_n=12, mode="hybrid", genre=genre)
    elif mode == "collaborative":
        recs = cinema.recommend(movie_id, top_n=12, mode="collaborative")
    else:
        recs = cinema.recommend(movie_id, top_n=12, mode="content")
    
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
async def discover_content(content_type: str, limit: int = 24, offset: int = 0):
    """Serve a random selection of content for the home page."""
    engine = registry.get_engine(content_type)
    if not engine:
         raise HTTPException(status_code=404, detail=f"Category '{content_type}' is not active.")
    
    results = engine.discover(limit=limit, offset=offset)
    
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
