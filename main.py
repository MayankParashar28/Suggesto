import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from modules.movie_recommender import MovieEngine
from modules.collab_recommender import CollabEngine
from modules.hybrid_recommender import HybridEngine
from typing import List, Dict, Any, Optional

import json
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")

app = FastAPI(title="Discovery API", version="1.0.0")

# 1. Metadata Cache Layer (Saves API hits)
CACHE_FILE = "models/metadata_cache.json"
metadata_cache = {}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r") as f:
            metadata_cache = json.load(f)
    except: pass

def save_metadata_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(metadata_cache, f)

class CacheUpdate(BaseModel):
    tmdbId: int
    data: dict

@app.post("/api/v1/metadata/cache")
async def update_metadata_cache(payload: CacheUpdate):
    metadata_cache[str(payload.tmdbId)] = payload.data
    save_metadata_cache()
    return {"status": "Cached"}

# 1. Initialize Engines
print("🚀 Initializing Recommendation Hub...")
movie_engine = MovieEngine(data_path="processed/", model_path="models/")
collab_engine = CollabEngine(data_path="processed/", model_path="models/")
hybrid_engine = HybridEngine(movie_engine, collab_engine)


# 2. TMDB Proxy (Secures API Key)
@app.get("/api/v1/tmdb/movie/{tmdb_id}")
async def get_tmdb_movie(tmdb_id: int):
    """Proxy request to TMDB to hide API key from frontend."""
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB API key not configured.")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                params={"api_key": TMDB_API_KEY}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="TMDB API error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# 3. API Routes
@app.get("/api/v1/movies/search")
async def search_movies(q: str = Query(..., min_length=2)):
    """Search for movies by part of the title."""
    results = movie_engine.search(q, limit=10)
    return {"results": results}

@app.get("/api/v1/movies/recommend/{movie_id}")
async def recommend_movies(movie_id: int, mode: str = Query("hybrid", pattern="^(content|collaborative|hybrid)$"), genre: Optional[str] = None):
    """Generate recommendations for a specific movieId."""
    if mode == "hybrid":
        recommendations = hybrid_engine.recommend(movie_id, top_n=12, genre=genre)
    elif mode == "collaborative":
        recommendations = collab_engine.recommend(movie_id, top_n=12)
    else:
        recommendations = movie_engine.recommend(movie_id, top_n=12)
        
    if not recommendations:
        # Fallback cascade logic
        if mode in ["hybrid", "collaborative"]:
             recommendations = movie_engine.recommend(movie_id, top_n=12)
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="Movie not found or recommendations unavailable.")

    for rec in recommendations:
        tid = str(rec.get("tmdbId"))
        if tid in metadata_cache:
            rec["cached"] = metadata_cache[tid]
            
    return {"recommendations": recommendations, "mode": mode, "genre": genre}

# 3. Static Files & Root
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def read_root():
    """Redirect root to the frontend dashboard."""
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
