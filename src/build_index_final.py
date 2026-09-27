import os
import time
import shutil
import numpy as np
import pandas as pd
import faiss
import torch
from pathlib import Path
from src.model.encoder import ImageEncoder

CSV_PATH = Path("data/catalogue/etsy/catalogue_clean.csv")
INDEX_DIR = Path("data/index")
INDEX_PATH = INDEX_DIR / "etsy_clip.index"
METADATA_PATH = INDEX_DIR / "etsy_index_metadata.csv"
BACKUP_INDEX_PATH = INDEX_DIR / "etsy_clip_3977.index"
BACKUP_METADATA_PATH = INDEX_DIR / "etsy_index_metadata_3977.csv"

def build_index():
    print("--- Building FAISS Index for Final Catalogue ---")
    start_time = time.time()
    
    if not CSV_PATH.exists():
        print(f"Error: Could not find cleaned catalogue at {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # 8. Backup old index
    if INDEX_PATH.exists() and not BACKUP_INDEX_PATH.exists():
        print(f"Backing up index to {BACKUP_INDEX_PATH}")
        shutil.copy2(INDEX_PATH, BACKUP_INDEX_PATH)
    if METADATA_PATH.exists() and not BACKUP_METADATA_PATH.exists():
        print(f"Backing up metadata to {BACKUP_METADATA_PATH}")
        shutil.copy2(METADATA_PATH, BACKUP_METADATA_PATH)
    
    # Check if CPU
    if torch.cuda.is_available():
        print("WARNING: CUDA is available, but CPU is requested. Using CPU!")
    
    encoder = ImageEncoder()
    # Ensure encoder runs on CPU (encoder might use device='cpu' internally if USE_TORCH=1)
    
    embeddings = []
    metadata = []
    failed_images = []
    
    expected_items = 5157
    print(f"Encoding {len(df)} images... (Expected {expected_items})")
    
    encode_times = []
    
    for index, row in df.iterrows():
        if index % 100 == 0:
            print(f"Processing {index}/{len(df)}...")
            
        img_path = str(row['local_image_path']).replace('\\', '/')
        
        t0 = time.time()
        emb = encoder.encode(img_path)
        t1 = time.time()
        
        if emb is not None:
            encode_times.append(t1 - t0)
            embeddings.append(emb[0])
            metadata.append(row.to_dict())
        else:
            failed_images.append(img_path)
            
    if not embeddings:
        print("Error: No embeddings were generated.")
        return
        
    embeddings_np = np.array(embeddings, dtype=np.float32)
    d = embeddings_np.shape[1] 
    
    # Check normalization
    norms = np.linalg.norm(embeddings_np, axis=1)
    avg_norm = np.mean(norms)
    print(f"Average vector norm before normalization: {avg_norm}")
    
    # Force L2 Normalization in case it isn't (though CLIP embeddings are often normalized)
    faiss.normalize_L2(embeddings_np)
    
    norms_after = np.linalg.norm(embeddings_np, axis=1)
    avg_norm_after = np.mean(norms_after)
    print(f"Average vector norm after FAISS normalization: {avg_norm_after}")
    
    print("Building IndexFlatIP...")
    index = faiss.IndexFlatIP(d)
    index.add(embeddings_np)
    
    print("Saving Index and Metadata...")
    faiss.write_index(index, str(INDEX_PATH))
    
    metadata_df = pd.DataFrame(metadata)
    # Ensure listing_id is string and unique
    if 'item_id' in metadata_df.columns and 'listing_id' not in metadata_df.columns:
        metadata_df = metadata_df.rename(columns={'item_id': 'listing_id'})
        
    # Strip "etsy_" prefix if present to ensure proper listing_id
    metadata_df['listing_id'] = metadata_df['listing_id'].astype(str).str.replace('etsy_', '')
    
    metadata_df['faiss_id'] = range(len(metadata_df))
    metadata_df.to_csv(METADATA_PATH, index=False)
    
    total_time = time.time() - start_time
    avg_encode_time = sum(encode_times) / len(encode_times) if encode_times else 0
    index_size_mb = os.path.getsize(INDEX_PATH) / (1024 * 1024)
    metadata_size_mb = os.path.getsize(METADATA_PATH) / (1024 * 1024)
    
    print("\n" + "="*40)
    print("INDEXING COMPLETE")
    print("="*40)
    print(f"Total catalogue products: {len(df)}")
    print(f"Vectors generated: {len(embeddings)}")
    print(f"Failed images: {len(failed_images)}")
    if failed_images:
        for f in failed_images:
            print(f"  - {f}")
            
    print(f"Embedding dimension: {d}")
    print(f"Index type: IndexFlatIP")
    print(f"Index size: {index_size_mb:.2f} MB")
    print(f"Average encoding time per image: {avg_encode_time*1000:.2f} ms")
    print(f"Total build time: {total_time:.2f} seconds")
    
    # Validations
    assert len(df) == expected_items, f"Expected {expected_items} items, got {len(df)}"
    assert len(embeddings) == expected_items, f"Missing embeddings! Got {len(embeddings)}"
    assert d == 512, f"Expected 512 dimensions, got {d}"
    assert index.ntotal == expected_items, f"FAISS index contains {index.ntotal} vectors, expected {expected_items}"
    assert len(metadata_df) == expected_items, f"Metadata contains {len(metadata_df)} rows, expected {expected_items}"
    
    assert metadata_df['listing_id'].nunique() == len(metadata_df), "listing_id is not unique in metadata"
    
    for img_path in metadata_df['local_image_path']:
        assert os.path.exists(img_path), f"Image path does not exist: {img_path}"
    
    print("All validations PASSED.")
    
    # 10. Sanity check: Retrieve a few catalogue images
    print("\n--- SANITY CHECK ---")
    sanity_results = []
    
    for test_idx in range(5):
        q_emb = embeddings_np[test_idx:test_idx+1]
        D, I = index.search(q_emb, 1)
        sim = D[0][0]
        retrieved_idx = I[0][0]
        
        expected_id = metadata_df.iloc[test_idx]['listing_id']
        retrieved_id = metadata_df.iloc[retrieved_idx]['listing_id']
        
        status = "PASS" if retrieved_idx == test_idx and np.isclose(sim, 1.0, atol=1e-3) else "FAIL"
        res_str = f"Image {test_idx} (ID: {expected_id}) -> Top match ID: {retrieved_id} (Sim: {sim:.4f}) [{status}]"
        print(res_str)
        sanity_results.append(res_str)
        
    # Generate report
    report_path = INDEX_DIR / "final_index_report.md"
    with open(report_path, "w") as f:
        f.write("# Final Index Report\n\n")
        f.write(f"- **Catalogue Size**: {len(df)}\n")
        f.write(f"- **Model**: openai/clip-vit-base-patch32\n")
        f.write(f"- **Embedding Dimension**: {d}\n")
        f.write(f"- **Index Type**: IndexFlatIP\n")
        f.write(f"- **Build Time**: {total_time:.2f} seconds\n")
        f.write(f"- **Average Encoding Time**: {avg_encode_time*1000:.2f} ms/image\n")
        f.write(f"- **Index Size**: {index_size_mb:.2f} MB\n")
        f.write(f"- **Metadata Size**: {metadata_size_mb:.2f} MB\n")
        
        f.write("\n## Verification Results\n")
        f.write("- Vector count matches metadata count (5157).\n")
        f.write("- All listing IDs are unique.\n")
        f.write(f"- Vector norms after normalization: {avg_norm_after:.4f} (approx 1.0)\n")
        f.write("- All metadata image paths exist on disk.\n")
        f.write("- Every catalogue listing has an embedding.\n")
        
        f.write("\n## Exact Image Sanity Check\n")
        for res in sanity_results:
            f.write(f"- {res}\n")
            
    print(f"\nSaved report to {report_path}")

if __name__ == "__main__":
    build_index()
