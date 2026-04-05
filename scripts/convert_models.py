import os
import numpy as np
import scipy.sparse as sp

def convert_to_numpy_sparse(model_path="models/"):
    npz_path = os.path.join(model_path, "tfidf_matrix.npz")
    if not os.path.exists(npz_path):
        print(f"❌ Could not find {npz_path}")
        return

    print(f"🔄 Loading {npz_path}...")
    matrix = sp.load_npz(npz_path)
    
    # Ensure it's in CSR format for fast row access
    csr = matrix.tocsr()
    
    print("💾 Saving CSR components to .npy...")
    np.save(os.path.join(model_path, "tfidf_data.npy"), csr.data)
    np.save(os.path.join(model_path, "tfidf_indices.npy"), csr.indices)
    np.save(os.path.join(model_path, "tfidf_indptr.npy"), csr.indptr)
    
    # Save shape separately
    with open(os.path.join(model_path, "tfidf_shape.txt"), "w") as f:
        f.write(f"{csr.shape[0]},{csr.shape[1]}")

    print("✅ Conversion complete! You can now remove scipy.")

if __name__ == "__main__":
    convert_to_numpy_sparse()
