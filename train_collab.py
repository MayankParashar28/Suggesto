import pandas as pd
import numpy as np
import time
import pickle
import os
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

# Configuration
DATA_DIR = "processed"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_collaborative_engine():
    print("⏳ Loading 32M ratings (Efficient Load)...")
    t_start = time.time()
    
    # Load only necessary columns with optimized dtypes
    ratings = pd.read_csv(
        f"{DATA_DIR}/ratings_filtered.csv", 
        usecols=["userId", "movieId", "rating"],
        dtype={"userId": "int32", "movieId": "int32", "rating": "float32"}
    )
    
    print(f"🏗️ Mapping sparse indices...")
    
    # Create categorical mappings for sparse matrix indices
    user_c = pd.Categorical(ratings["userId"])
    movie_c = pd.Categorical(ratings["movieId"])
    
    # Build the CSR Matrix (Users x Movies)
    row_codes = user_c.codes
    col_codes = movie_c.codes
    
    X = csr_matrix(
        (ratings["rating"], (row_codes, col_codes)), 
        shape=(user_c.categories.size, movie_c.categories.size)
    )
    
    movie_id_mapping = dict(enumerate(movie_c.categories))
    movie_to_code = {v: k for k, v in movie_id_mapping.items()}
    
    # Clean up memory immediately
    del ratings, user_c, movie_c
    
    print("⚡ Training Matrix Factorization (Latent Space = 100)...")
    # Training on the Transpose (Movies x Users) to get Movie Factors
    svd = TruncatedSVD(n_components=100, algorithm="randomized", random_state=42)
    movie_factors = svd.fit_transform(X.T)
    
    # Standardize factors (Pre-normalization for Cosine Similarity)
    norms = np.linalg.norm(movie_factors, axis=1, keepdims=True)
    movie_factors = np.divide(movie_factors, norms, out=np.zeros_like(movie_factors), where=norms!=0)
    
    # Save Assets
    print(f"💾 Saving pre-normalized assets to ./{MODEL_DIR}/...")
    np.save(f"{MODEL_DIR}/collab_factors.npy", movie_factors)
    
    with open(f"{MODEL_DIR}/movie_id_map.pkl", "wb") as f:
        pickle.dump(movie_id_mapping, f)
        
    with open(f"{MODEL_DIR}/movie_to_code.pkl", "wb") as f:
        pickle.dump(movie_to_code, f)
        
    print(f"✅ Collaborative Filtering Engine trained in {time.time() - t_start:.2f}s")
    print(f"   Matrix Shape: {X.shape}")
    print(f"   Factors Shape: {movie_factors.shape}")

if __name__ == "__main__":
    train_collaborative_engine()
