import ast
import pandas as pd

def parse_list_field(val):
    """Safely parse stringified Python lists from CSV back to real lists."""
    if isinstance(val, list):
        return val
    if not isinstance(val, str) or val in ("[]", "(no genres listed)"):
        return []
    try:
        parsed = ast.literal_eval(val)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        # Fallback for manual pipe-separated strings
        return [g.strip() for g in val.split("|") if g.strip()]

def format_movie_response(row, score=None, mode="content"):
    """Standardizes the movie dictionary format used across all engines."""
    return {
        "movieId": int(row["movieId"]),
        "title": row["title"],
        "genres": row["genres"],
        "releaseYear": (
            int(row["release_year"])
            if pd.notna(row["release_year"])
            else None
        ),
        "tmdbId": int(row["tmdbId"]),
        "imdbId": int(row["imdbId"]),
        "similarity": score,
        "mode": mode,
    }
