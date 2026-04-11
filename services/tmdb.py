import os
import json
import asyncio
import httpx
from fastapi import HTTPException
from typing import Dict, Any, Optional, List

class TMDBService:
    def __init__(self, cache_file: str = "models/metadata_cache.json"):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
        self.cache_file = cache_file
        self.dirty = False
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
        if not self.dirty:
            return
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
            self.dirty = False
        except Exception as e:
            print(f"⚠️ Cache save failed (expected on read-only filesystems like Vercel): {e}")

    async def get_movie_details(self, tmdb_id: int) -> Dict[str, Any]:
        """Fetch movie details from TMDB with proxying and error handling."""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="TMDB API key not configured.")

        # Check cache first
        if str(tmdb_id) in self.cache:
            return self.cache[str(tmdb_id)]

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params={"api_key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                
                # Auto-cache new results (O2: save deferred to batch)
                self.cache[str(tmdb_id)] = data
                self.dirty = True
                
                return data
            except httpx.HTTPStatusError as e:
                # Movie not found in TMDB — cache a minimal stub to avoid retries
                stub = {"id": tmdb_id, "title": "Unknown", "poster_path": None, "overview": "", "vote_average": 0}
                self.cache[str(tmdb_id)] = stub
                self.dirty = True
                return stub
            except Exception as e:
                # Network/timeout errors — return stub but don't cache (retry later)
                return {"id": tmdb_id, "title": "Unknown", "poster_path": None, "overview": "", "vote_average": 0}

    async def batch_get_movie_details(self, tmdb_ids: List[int]) -> Dict[str, Any]:
        """Fetch multiple movies concurrently. Returns {tmdbId: data} dict."""
        results = {}
        to_fetch = []

        # Check cache first
        for tid in tmdb_ids:
            key = str(tid)
            if key in self.cache:
                results[key] = self.cache[key]
            else:
                to_fetch.append(tid)

        if not to_fetch or not self.api_key:
            return results

        # Fetch uncached movies concurrently (max 8 at a time)
        semaphore = asyncio.Semaphore(8)
        
        async def fetch_one(client: httpx.AsyncClient, tid: int):
            async with semaphore:
                try:
                    response = await client.get(
                        f"{self.base_url}/movie/{tid}",
                        params={"api_key": self.api_key},
                        timeout=5.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    self.cache[str(tid)] = data
                    self.dirty = True
                    return str(tid), data
                except Exception:
                    return str(tid), None

        async with httpx.AsyncClient() as client:
            tasks = [fetch_one(client, tid) for tid in to_fetch]
            fetched = await asyncio.gather(*tasks)
            
        for key, data in fetched:
            if data:
                results[key] = data

        # Save cache after batch fetch
        self._save_cache()
        return results

    def enrich_recommendations(self, recommendations: list) -> list:
        """Inject cached metadata into recommendation objects for performance."""
        for rec in recommendations:
            tid = str(rec.get("tmdbId"))
            if tid in self.cache:
                rec["cached"] = self.cache[tid]
        return recommendations

    def update_cache(self, tmdb_id: int, data: dict):
        self.cache[str(tmdb_id)] = data
        self.dirty = True
        self._save_cache()
