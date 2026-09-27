import os
import time
import pandas as pd
import faiss
import numpy as np
from pathlib import Path
from PIL import Image
from src.model.encoder import ImageEncoder

# Paths
INPUT_DIR = Path("data/stumper/physical_reference")
INDEX_PATH = Path("data/index/etsy_clip.index")
METADATA_PATH = Path("data/index/etsy_index_metadata.csv")

RESULTS_DIR = Path("results/real_world_test")
CSV_OUT = RESULTS_DIR / "results.csv"
REPORT_OUT = RESULTS_DIR / "report.md"

def get_crops(img):
    """Returns a dictionary of deterministic crops for an image."""
    width, height = img.size
    
    # 1. Full Image
    full = img.copy()
    
    # 2. Center Crop (e.g. 60% of center)
    cw, ch = int(width * 0.6), int(height * 0.6)
    left = (width - cw) // 2
    top = (height - ch) // 2
    center_crop = img.crop((left, top, left + cw, top + ch))
    
    # 3. Upper/Central Object-Focused Crop (often jewelry is placed slightly above center)
    top_upper = int(height * 0.2)
    bottom_upper = int(height * 0.7)
    left_upper = int(width * 0.2)
    right_upper = int(width * 0.8)
    upper_crop = img.crop((left_upper, top_upper, right_upper, bottom_upper))
    
    # 4. Tighter Central Crop (40% of center)
    tw, th = int(width * 0.4), int(height * 0.4)
    tl = (width - tw) // 2
    tt = (height - th) // 2
    tight_crop = img.crop((tl, tt, tl + tw, tt + th))
    
    return {
        "full": full,
        "center": center_crop,
        "upper": upper_crop,
        "tight": tight_crop
    }

def get_unique_top_k(D, I, metadata_df, k=5):
    results = []
    seen = set()
    
    for i in range(len(I)):
        idx = I[i]
        sim = D[i]
        if idx < 0 or idx >= len(metadata_df): continue
        row = metadata_df.iloc[idx]
        l_id = str(row['listing_id'])
        if l_id not in seen:
            seen.add(l_id)
            results.append({
                'listing_id': l_id,
                'category': row['category'],
                'similarity': float(sim)
            })
        if len(results) == k:
            break
    return results

def main():
    print("Running Real-World Stress Test...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    images = [
        INPUT_DIR / "test1.jpeg",
        INPUT_DIR / "test2.jpeg",
        INPUT_DIR / "test4.jpeg",
        INPUT_DIR / "test5.jpeg",
    ]
    
    print("Loading FAISS index and metadata...")
    index = faiss.read_index(str(INDEX_PATH))
    metadata_df = pd.read_csv(METADATA_PATH)
    
    # Ensure string IDs
    if 'listing_id' not in metadata_df.columns and 'item_id' in metadata_df.columns:
        metadata_df['listing_id'] = metadata_df['item_id']
    
    encoder = ImageEncoder()
    
    all_results = []
    
    for img_path in images:
        if not img_path.exists():
            print(f"Skipping {img_path} - not found.")
            continue
            
        print(f"Processing {img_path.name}...")
        
        # Load PIL image once to avoid disk I/O overhead in timing
        img = Image.open(img_path).convert("RGB")
        crops = get_crops(img)
        
        import tempfile
        # --- BASELINE (Full Image) ---
        t0 = time.perf_counter()
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            crops['full'].save(tmp.name)
            tmp_full = tmp.name
            
        b_emb = encoder.encode(tmp_full)
        t1 = time.perf_counter()
        
        faiss.normalize_L2(b_emb)
        D, I = index.search(b_emb, k=20)
        t2 = time.perf_counter()
        os.remove(tmp_full)
        
        baseline_time_enc = (t1 - t0) * 1000
        baseline_time_search = (t2 - t1) * 1000
        
        b_top_k = get_unique_top_k(D[0], I[0], metadata_df, k=5)
        
        # --- MULTI-CROP (Best of all crops) ---
        mc_t0 = time.perf_counter()
        mc_best_sim = -1.0
        mc_best_top_k = []
        
        for c_name, c_img in crops.items():
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                c_img.save(tmp.name)
                tmp_c = tmp.name
                
            c_emb = encoder.encode(tmp_c)
            faiss.normalize_L2(c_emb)
            c_D, c_I = index.search(c_emb, k=20)
            os.remove(tmp_c)
            
            c_top_k = get_unique_top_k(c_D[0], c_I[0], metadata_df, k=5)
            if c_top_k and c_top_k[0]['similarity'] > mc_best_sim:
                mc_best_sim = c_top_k[0]['similarity']
                mc_best_top_k = c_top_k
                
        mc_t1 = time.perf_counter()
        
        # Multi-crop time is total time to encode and search all crops
        # But we also need to report overall latency. The prompt asks for:
        # encoding_time_ms, faiss_search_time_ms, total_time_ms
        # Since baseline is the standard, we will record the baseline latencies as the standard query latency,
        # but the prompt just says "total_time_ms". I'll report the multi-crop total time as well if needed, 
        # or just report baseline time. Let's record baseline times for the latency stats.
        
        enc_time = baseline_time_enc
        search_time = baseline_time_search
        tot_time = enc_time + search_time
        
        if not b_top_k or not mc_best_top_k:
            continue
            
        all_results.append({
            'filename': img_path.name,
            'baseline_top1_listing_id': b_top_k[0]['listing_id'],
            'baseline_top1_category': b_top_k[0]['category'],
            'baseline_top1_similarity': b_top_k[0]['similarity'],
            'baseline_top5_listing_ids': "|".join([x['listing_id'] for x in b_top_k]),
            'multicrop_top1_listing_id': mc_best_top_k[0]['listing_id'],
            'multicrop_top1_category': mc_best_top_k[0]['category'],
            'multicrop_top1_similarity': mc_best_top_k[0]['similarity'],
            'multicrop_top5_listing_ids': "|".join([x['listing_id'] for x in mc_best_top_k]),
            'encoding_time_ms': enc_time,
            'faiss_search_time_ms': search_time,
            'total_time_ms': tot_time
        })
        
    df = pd.DataFrame(all_results)
    df.to_csv(CSV_OUT, index=False)
    
    # --- Stats ---
    avg_total = df['total_time_ms'].mean()
    med_total = df['total_time_ms'].median()
    avg_enc = df['encoding_time_ms'].mean()
    avg_search = df['faiss_search_time_ms'].mean()
    
    agreement = (df['baseline_top1_listing_id'] == df['multicrop_top1_listing_id']).sum()
    df['sim_diff'] = df['multicrop_top1_similarity'] - df['baseline_top1_similarity']
    avg_sim_diff = df['sim_diff'].mean()
    
    # --- Report ---
    report = f"""# Real-World Exploratory Stress Test

**Disclaimer:** 
- The 4 photos used in this test (`test1.jpeg`, `test2.jpeg`, `test4.jpeg`, `test5.jpeg`) have **NO verified catalogue ground truth**. 
- These images are purely exploratory and do NOT represent the final 100-image Stumper benchmark. 
- No Top-1 accuracy is calculated, and model predictions are not labeled as "correct" or "incorrect." 
- The production FAISS index and catalogue were strictly untouched.

## Experiment Setup
- **Baseline**: Full image passed directly to the CLIP model.
- **Multi-crop**: Evaluated the full image plus 3 deterministic crops (center, upper-center, tight-center). The crop yielding the highest Top-1 inner product similarity was selected.

## Summary Statistics

### Latency (Baseline Query)
* **Average Encoding Time**: {avg_enc:.2f} ms
* **Average FAISS Search**: {avg_search:.2f} ms
* **Average Total Latency**: {avg_total:.2f} ms
* **Median Total Latency**: {med_total:.2f} ms

### Baseline vs. Multi-crop Behavior
* **Top-1 Agreement**: {agreement} out of {len(df)} queries returned the exact same Top-1 listing ID.
* **Average Similarity Difference**: {avg_sim_diff:+.4f} (Multi-crop vs Baseline)

## Detailed Results

"""
    for _, row in df.iterrows():
        report += f"### {row['filename']}\n"
        report += f"- **Baseline Top-1**: ID `{row['baseline_top1_listing_id']}` ({row['baseline_top1_category']}) | Sim: {row['baseline_top1_similarity']:.4f}\n"
        report += f"- **Multicrop Top-1**: ID `{row['multicrop_top1_listing_id']}` ({row['multicrop_top1_category']}) | Sim: {row['multicrop_top1_similarity']:.4f}\n"
        
        if row['baseline_top1_listing_id'] != row['multicrop_top1_listing_id']:
            report += f"- *Result changed due to cropping.*\n"
        else:
            report += f"- *Result remained the same.*\n"
        report += "\n"

    with open(REPORT_OUT, "w") as f:
        f.write(report)
        
    print(f"\nDone! Saved to {CSV_OUT} and {REPORT_OUT}")

if __name__ == "__main__":
    main()
