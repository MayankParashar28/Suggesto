import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse as sp

def process_music(input_file="tracks_features.csv", output_path="processed/", model_path="models/"):
    print(f"🎸 Starting Music Preprocessing for {input_file}...")
    
    if not os.path.exists(output_path): os.makedirs(output_path)
    if not os.path.exists(model_path): os.makedirs(model_path)

    # 1. Load the massive 1.2M dataset
    # Only load columns we need to save memory
    cols = ['id', 'name', 'album', 'artists', 'year', 'release_date', 'tempo', 'energy', 'danceability', 'duration_ms', 'explicit']
    df = pd.read_csv(input_file, usecols=cols)
    print(f"   📊 Loaded {len(df):,} total tracks.")

    # 2. Filter to top 100k most recent (Vercel Optimization)
    df = df.sort_values('release_date', ascending=False).head(100000).reset_index(drop=True)
    print(f"   ✂️  Filtered to top {len(df):,} recent tracks for Sketchbook.")

    # 3. Create Content Signature for TF-IDF
    # Cleaning string lists like "['Artist A', 'Artist B']"
    df['artists_clean'] = df['artists'].str.replace("[", "").str.replace("]", "").str.replace("'", "").str.replace('"', "")
    df['content'] = df['name'].fillna('') + " " + df['artists_clean'].fillna('') + " " + df['album'].fillna('')
    df['content'] = df['content'].str.lower().str.strip()

    # 4. Generate TF-IDF Matrix
    print("   🧠 Building Music TF-IDF (Universal Discovery)...")
    tfidf = TfidfVectorizer(stop_words='english', max_features=20000)
    tfidf_matrix = tfidf.fit_transform(df['content'])
    
    # 5. Save Slim Processed Data (CSV for Suggesto Registry)
    # We only need enough info to show on the card
    slim_df = df[['id', 'name', 'artists_clean', 'album', 'year', 'tempo', 'energy', 'danceability', 'duration_ms', 'explicit']]
    slim_df.to_csv(os.path.join(output_path, "songs_processed.csv"), index=False)
    print(f"   💾 Saved songs_processed.csv")

    # 6. Save Zero-Scipy Numpy Components
    csr = tfidf_matrix.tocsr()
    np.save(os.path.join(model_path, "songs_tfidf_data.npy"), csr.data)
    np.save(os.path.join(model_path, "songs_tfidf_indices.npy"), csr.indices)
    np.save(os.path.join(model_path, "songs_tfidf_indptr.npy"), csr.indptr)
    
    # Save shape separately
    with open(os.path.join(model_path, "songs_tfidf_shape.txt"), "w") as f:
        f.write(f"{csr.shape[0]},{csr.shape[1]}")
    
    print(f"   ✅ Music Preprocessing Complete! Matrix Shape: {csr.shape}")

if __name__ == "__main__":
    process_music()
