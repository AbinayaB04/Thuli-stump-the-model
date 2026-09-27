import os
import time
import pickle
import numpy as np
import pandas as pd
import faiss

# Import the encoder (assumes being run as a module from project root)
from src.model.encoder import ImageEncoder

CSV_PATH = "data/catalogue/catalogue_clean.csv"
EMBEDDING_DIR = "data/embeddings"
INDEX_PATH = os.path.join(EMBEDDING_DIR, "catalogue.index")
METADATA_PATH = os.path.join(EMBEDDING_DIR, "metadata.pkl")

def build_index():
    print("--- Building FAISS Index ---")
    start_time = time.time()
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find cleaned catalogue at {CSV_PATH}")
        return None, None
        
    df = pd.read_csv(CSV_PATH)
    
    os.makedirs(EMBEDDING_DIR, exist_ok=True)
    
    # Initialize the encoder once
    encoder = ImageEncoder()
    
    embeddings = []
    metadata = []
    failed_images = []
    
    print(f"Encoding {len(df)} images...")
    
    # Encode every valid catalogue image
    for index, row in df.iterrows():
        # Reconstruct path reliably assuming script is run from project root
        filename = os.path.basename(str(row['local_image_path']).replace('\\', '/'))
        actual_path = os.path.join("data", "catalogue", "images", filename)
        
        emb = encoder.encode(actual_path)
        if emb is not None:
            # We take emb[0] because the encoder returns a batch of 1
            embeddings.append(emb[0])
            metadata.append(row.to_dict())
        else:
            failed_images.append(actual_path)
            
    if not embeddings:
        print("Error: No embeddings were generated.")
        return None, None
        
    # Convert list of 1D arrays into a 2D NumPy array
    embeddings_np = np.array(embeddings, dtype=np.float32)
    
    # The dimension is 512 for CLIP ViT-B/32
    d = embeddings_np.shape[1] 
    
    # Create the FAISS Index
    # We use IndexFlatIP (Inner Product).
    # Since all our embeddings are strictly L2-normalized in the encoder,
    # computing the inner product inherently yields the cosine similarity.
    index = faiss.IndexFlatIP(d)
    
    # Add vectors to the index
    index.add(embeddings_np)
    
    # Save the FAISS index to disk
    faiss.write_index(index, INDEX_PATH)
    
    # Save corresponding metadata exactly aligned with FAISS row positions
    with open(METADATA_PATH, 'wb') as f:
        pickle.dump(metadata, f)
        
    total_time = time.time() - start_time
    
    # Summary reporting
    print("\n--- Indexing Complete ---")
    print(f"Total catalogue images processed: {len(df)}")
    print(f"Successfully encoded: {len(metadata)}")
    if failed_images:
        print(f"Failed images: {len(failed_images)}")
        for f in failed_images:
            print(f"  - {f}")
    else:
        print("Failed images: 0")
        
    print(f"Embedding dimension: {d}")
    print(f"FAISS index type: IndexFlatIP")
    print(f"Number of vectors in index: {index.ntotal}")
    print(f"Total indexing time: {total_time:.2f} seconds")
    
    return index, metadata

if __name__ == "__main__":
    build_index()
