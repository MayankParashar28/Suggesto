import os
import json
import httpx
from fastapi import HTTPException
from typing import Dict, Any, Optional

class TMDBService:
    def __init__(self, cache_file: str = "models/metadata_cache.json"):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Cache load error: {e}")
        return {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"⚠️ Cache save failed (expected on read-only filesystems like Vercel): {e}")

    async def get_movie_details(self, tmdb_id: int) -> Dict[str, Any]:
        """Fetch movie details from TMDB with proxying and error handling."""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="TMDB API key not configured.")

        # Check cache first
        if str(tmdb_id) in self.cache:
            return self.cache[str(tmdb_id)]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params={"api_key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                
                # Auto-cache new results
                self.cache[str(tmdb_id)] = data
                self._save_cache()
                
                return data
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail="TMDB API error")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal TMDB Proxy Error: {str(e)}")

    def enrich_recommendations(self, recommendations: list) -> list:
        """Inject cached metadata into recommendation objects for performance."""
        for rec in recommendations:
            tid = str(rec.get("tmdbId"))
            if tid in self.cache:
                rec["cached"] = self.cache[tid]
        return recommendations

    def update_cache(self, tmdb_id: int, data: dict):
        self.cache[str(tmdb_id)] = data
        self._save_cache()
