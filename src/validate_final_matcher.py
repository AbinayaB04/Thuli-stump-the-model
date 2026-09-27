import os
import time
import numpy as np
import pandas as pd
import faiss
from pathlib import Path
from src.model.encoder import ImageEncoder

# Paths
INDEX_DIR = Path("data/index")
INDEX_PATH = INDEX_DIR / "etsy_clip.index"
METADATA_PATH = INDEX_DIR / "etsy_index_metadata.csv"

QUERIES_DIR = Path("data/queries/images")
RESULTS_DIR = Path("results/final_matcher")
CSV_OUT = RESULTS_DIR / "query_results.csv"
REPORT_OUT = RESULTS_DIR / "report.md"

QUERY_IMAGES = [
    "test1.jpeg", "test2.jpeg", "test3.jpeg",
    "test4.jpeg", "test5.jpeg", "test6.jpeg", "test8.jpeg"
]

def ensure_unique_top_k(D, I, metadata_df, k=5):
    # Given distances D and indices I for a single query (1D arrays)
    # Return unique Top K listings
    unique_results = []
    seen_listings = set()
    
    for i in range(len(I)):
        idx = I[i]
        sim = D[i]
        if idx < 0 or idx >= len(metadata_df): continue
        
        row = metadata_df.iloc[idx]
        listing_id = str(row.get('listing_id', ''))
        
        if listing_id not in seen_listings:
            seen_listings.add(listing_id)
            unique_results.append({
                'idx': idx,
                'listing_id': listing_id,
                'category': row.get('category', ''),
                'title': row.get('title', ''),
                'similarity': float(sim),
                'image_path': row.get('local_image_path', '')
            })
            
        if len(unique_results) == k:
            break
            
    return unique_results

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading final FAISS index and metadata...")
    index = faiss.read_index(str(INDEX_PATH))
    metadata_df = pd.read_csv(METADATA_PATH)
    
    print(f"Loaded index with {index.ntotal} vectors.")
    print(f"Loaded metadata with {len(metadata_df)} rows.")
    
    encoder = ImageEncoder()
    
    results = []
    
    encode_times = []
    search_times = []
    total_times = []
    
    print("\n--- Running Queries ---\n")
    
    for q_filename in QUERY_IMAGES:
        q_path = QUERIES_DIR / q_filename
        if not q_path.exists():
            print(f"Warning: {q_path} does not exist. Skipping.")
            continue
            
        print(f"Query: {q_filename}")
        
        # 1. Encoding
        t0 = time.time()
        q_emb = encoder.encode(str(q_path))
        if q_emb is None:
            print(f"Failed to encode {q_filename}")
            continue
            
        # Ensure L2 norm (same as build_index)
        faiss.normalize_L2(q_emb)
        t_encode = time.time()
        
        # 2. Searching
        # Get extra to guarantee 5 unique
        D, I = index.search(q_emb, k=20)
        t_search = time.time()
        
        total_time = t_search - t0
        encode_times.append(t_encode - t0)
        search_times.append(t_search - t_encode)
        total_times.append(total_time)
        
        # Filter Top-5 unique
        top5 = ensure_unique_top_k(D[0], I[0], metadata_df, k=5)
        
        for rank, match in enumerate(top5, 1):
            short_title = str(match['title'])[:50] + "..." if len(str(match['title'])) > 50 else str(match['title'])
            
            print(f"  Rank {rank}: ID: {match['listing_id']} | Cat: {match['category']} | Sim: {match['similarity']:.4f} | Title: {short_title}")
            
            results.append({
                'query_image': q_filename,
                'rank': rank,
                'listing_id': match['listing_id'],
                'category': match['category'],
                'similarity': match['similarity'],
                'image_path': match['image_path']
            })
            
    # Save CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(CSV_OUT, index=False)
    print(f"\nSaved CSV results to {CSV_OUT}")
    
    # Calculate Latencies
    avg_enc = np.mean(encode_times) * 1000
    med_enc = np.median(encode_times) * 1000
    
    avg_srch = np.mean(search_times) * 1000
    med_srch = np.median(search_times) * 1000
    
    avg_tot = np.mean(total_times) * 1000
    
    print(f"\n--- Latency Statistics (ms) ---")
    print(f"Average Encoding Time : {avg_enc:.2f} ms")
    print(f"Median Encoding Time  : {med_enc:.2f} ms")
    print(f"Average FAISS Search  : {avg_srch:.2f} ms")
    print(f"Median FAISS Search   : {med_srch:.2f} ms")
    print(f"Average Total Query   : {avg_tot:.2f} ms")
    
    # Generate Report
    with open(REPORT_OUT, "w") as f:
        f.write("# Final Matcher Validation Report\n\n")
        f.write(f"- **Final Catalogue Size**: {index.ntotal}\n")
        f.write("- **Model**: openai/clip-vit-base-patch32\n")
        f.write(f"- **Embedding Dimension**: {index.d}\n")
        f.write("- **FAISS Index Type**: IndexFlatIP\n")
        f.write("- **Top-5 Retrieval Behavior**: Returns 5 unique items based on Inner Product (Cosine Similarity) over L2 normalized vectors.\n\n")
        
        f.write("## Latency Statistics (ms)\n")
        f.write(f"- **Average Query Encoding Time**: {avg_enc:.2f} ms\n")
        f.write(f"- **Median Query Encoding Time**: {med_enc:.2f} ms\n")
        f.write(f"- **Average FAISS Search Time**: {avg_srch:.2f} ms\n")
        f.write(f"- **Median FAISS Search Time**: {med_srch:.2f} ms\n")
        f.write(f"- **Average Total Query Latency**: {avg_tot:.2f} ms\n\n")
        
        f.write("## Accuracy Note\n")
        f.write("> **IMPORTANT**: The 7-query results below are NOT accuracy measurements because verified ground truth is unavailable. This is an end-to-end functionality validation, not an accuracy evaluation.\n")
        
    print(f"Saved markdown report to {REPORT_OUT}")

if __name__ == "__main__":
    main()
