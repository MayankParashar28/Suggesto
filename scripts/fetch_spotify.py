import pandas as pd
from datasets import load_dataset
import numpy as np

def fetch_and_combine():
    print("⬇️ Loading General Spotify dataset (114k tracks)...")
    ds_gen = load_dataset("maharshipandya/spotify-tracks-dataset")
    df_gen = ds_gen['train'].to_pandas()
    
    # Rename columns for internal consistency
    df_gen = df_gen.rename(columns={
        'track_id': 'id',
        'track_name': 'name',
        'album_name': 'album'
    })

    # The dataset doesn't have 'year', so we'll generate one for sorting purposes
    # We'll use a random distribution to simulate a timeline
    df_gen['year'] = np.random.randint(1990, 2024, size=len(df_gen))

    print("⬇️ Filtering for Indian Music...")
    # Explicitly pull all regional genres to ensure priority
    indian_genres = ['indian', 'bollywood', 'hindi', 'tamil', 'telugu']
    df_indian = df_gen[df_gen['track_genre'].str.lower().isin(indian_genres)].copy()
    
    # Also search by common Indian artist keywords in case they are misclassified
    indian_artists = ['Arijit Singh', 'A.R. Rahman', 'Shreya Ghoshal', 'Pritam', 'Atif Aslam', 'Lata Mangeshkar', 'Kishore Kumar', 'Sonu Nigam', 'Alka Yagnik', 'Udit Narayan', 'Ankit Tiwari', 'Neha Kakkar', 'Badshah', 'Sidhu Moose Wala']
    artist_query = '|'.join(indian_artists)
    df_artist_hits = df_gen[df_gen['artists'].str.contains(artist_query, case=False, na=False)].copy()
    
    df_indian = pd.concat([df_indian, df_artist_hits]).drop_duplicates(subset=['id'])
    
    print(f"✅ Found {len(df_indian)} Indian/Regional tracks.")

    # Combine datasets: Prioritize Indian tracks so they don't get lost in similarities
    df_combined = pd.concat([df_indian, df_gen]).drop_duplicates(subset=['id']).reset_index(drop=True)

    # Approximate release info
    df_combined['release_date'] = df_combined['year'].astype(str) + "-01-01"

    cols = ['id', 'name', 'album', 'artists', 'year', 'release_date', 'tempo', 'energy', 'danceability', 'duration_ms', 'explicit']
    df_out = df_combined[cols]

    df_out.to_csv("tracks_features.csv", index=False)
    print(f"💿 Saved combined dataset to tracks_features.csv — Total: {len(df_out)} tracks.")

if __name__ == "__main__":
    fetch_and_combine()
