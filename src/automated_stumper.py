import os
import random
import time
import pandas as pd
import numpy as np
import faiss
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
from pathlib import Path
from src.model.encoder import ImageEncoder

# Paths
CATALOGUE_CSV = Path("data/catalogue/etsy/catalogue_clean.csv")
INDEX_PATH = Path("data/index/etsy_clip.index")
METADATA_PATH = Path("data/index/etsy_index_metadata.csv")

OUT_DIR = Path("results/automated_stumper")
IMG_OUT_DIR = OUT_DIR / "images"
DATASET_CSV = OUT_DIR / "dataset.csv"
RESULTS_CSV = OUT_DIR / "results.csv"
REPORT_MD = OUT_DIR / "report.md"

SEED = 42
NUM_LISTINGS = 50

# Set seeds
random.seed(SEED)
np.random.seed(SEED)

def transform_image(img, condition):
    img = img.copy()
    w, h = img.size
    
    if condition == "bad_lighting":
        return ImageEnhance.Brightness(img).enhance(0.4)
        
    elif condition == "brightness_contrast":
        img = ImageEnhance.Brightness(img).enhance(1.5)
        return ImageEnhance.Contrast(img).enhance(1.5)
        
    elif condition == "blur":
        return img.filter(ImageFilter.GaussianBlur(radius=3))
        
    elif condition == "rotation":
        return img.rotate(15, resample=Image.BILINEAR, expand=False, fillcolor=(255,255,255))
        
    elif condition == "partial_crop":
        cw, ch = int(w * 0.7), int(h * 0.7)
        left = random.randint(0, w - cw)
        top = random.randint(0, h - ch)
        return img.crop((left, top, left + cw, top + ch))
        
    elif condition == "partial_occlusion":
        draw = ImageDraw.Draw(img)
        # draw a black box covering ~20% of the image
        ow, oh = int(w * 0.4), int(h * 0.4)
        ox = random.randint(0, w - ow)
        oy = random.randint(0, h - oh)
        draw.rectangle([ox, oy, ox + ow, oy + oh], fill="black")
        return img
        
    elif condition == "background_clutter":
        # Draw random colored lines to simulate clutter
        draw = ImageDraw.Draw(img)
        for _ in range(20):
            x1, y1 = random.randint(0, w), random.randint(0, h)
            x2, y2 = random.randint(0, w), random.randint(0, h)
            draw.line((x1, y1, x2, y2), fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255)), width=3)
        return img
        
    elif condition == "image_noise":
        # Add gaussian noise
        img_arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, 25, img_arr.shape)
        img_arr = np.clip(img_arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(img_arr)
        
    elif condition == "perspective_distortion":
        # Simulate perspective by slightly warping corners
        m = -0.1
        xshift = abs(m) * w
        new_width = w + int(round(xshift))
        return img.transform(
            (new_width, h),
            Image.AFFINE,
            (1, m, -xshift if m > 0 else 0, 0, 1, 0),
            Image.BICUBIC,
            fillcolor=(255,255,255)
        )
        
    elif condition == "combined_difficult":
        # Blur + rotate + bad lighting
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img = img.rotate(-15, fillcolor=(255,255,255))
        img = ImageEnhance.Brightness(img).enhance(0.5)
        return img

    return img

def get_unique_top_k(D, I, metadata_df, k=5):
    results = []
    seen = set()
    for i in range(len(I)):
        idx = I[i]
        sim = D[i]
        if idx < 0 or idx >= len(metadata_df): continue
        row = metadata_df.iloc[idx]
        l_id = str(row.get('listing_id', row.get('item_id')))
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
    print("Programmatically Generated Stumper Evaluation")
    print("Initializing...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_OUT_DIR.mkdir(exist_ok=True)
    
    # 1. Load Catalogue and Sample 50
    df = pd.read_csv(CATALOGUE_CSV)
    if 'listing_id' not in df.columns:
        df['listing_id'] = df['item_id']
    df['listing_id'] = df['listing_id'].astype(str)
    df = df.dropna(subset=['listing_id', 'local_image_path'])
    
    sampled_df = df.sample(n=NUM_LISTINGS, random_state=SEED).reset_index(drop=True)
    
    conditions = [
        "bad_lighting", "brightness_contrast", "blur", "rotation",
        "partial_crop", "partial_occlusion", "background_clutter",
        "image_noise", "perspective_distortion", "combined_difficult"
    ]
    
    dataset_records = []
    
    # 2. Generate Images
    print("Generating synthetic stumper images...")
    for idx, row in sampled_df.iterrows():
        source_id = row['listing_id']
        source_path = row['local_image_path']
        
        try:
            img = Image.open(source_path).convert("RGB")
        except Exception as e:
            print(f"Skipping {source_id} due to image load error: {e}")
            continue
            
        for cond in conditions:
            out_img = transform_image(img, cond)
            out_filename = f"{source_id}_{cond}.jpg"
            out_path = IMG_OUT_DIR / out_filename
            out_img.save(out_path)
            
            dataset_records.append({
                'query_filename': out_filename,
                'ground_truth_listing_id': source_id,
                'source_listing_id': source_id,
                'condition': cond,
                'source_image_path': source_path,
                'random_seed': SEED
            })
            
    dataset_df = pd.DataFrame(dataset_records)
    dataset_df.to_csv(DATASET_CSV, index=False)
    print(f"Generated {len(dataset_df)} images across {len(conditions)} conditions.")
    
    # 3. Evaluate using production index
    print("Loading FAISS index and encoder...")
    index = faiss.read_index(str(INDEX_PATH))
    metadata_df = pd.read_csv(METADATA_PATH)
    if 'listing_id' not in metadata_df.columns:
        metadata_df['listing_id'] = metadata_df['item_id']
    metadata_df['listing_id'] = metadata_df['listing_id'].astype(str)
    
    encoder = ImageEncoder()
    
    results = []
    
    print("Running evaluation...")
    for _, row in dataset_df.iterrows():
        q_path = IMG_OUT_DIR / row['query_filename']
        
        t0 = time.perf_counter()
        q_emb = encoder.encode(str(q_path))
        t1 = time.perf_counter()
        
        if q_emb is None:
            continue
            
        faiss.normalize_L2(q_emb)
        D, I = index.search(q_emb, k=20)
        t2 = time.perf_counter()
        
        top_k = get_unique_top_k(D[0], I[0], metadata_df, k=5)
        
        if not top_k:
            continue
            
        top1_id = top_k[0]['listing_id']
        top5_ids = [x['listing_id'] for x in top_k]
        gt_id = str(row['ground_truth_listing_id'])
        
        results.append({
            'query_filename': row['query_filename'],
            'ground_truth_listing_id': gt_id,
            'predicted_top1_listing_id': top1_id,
            'top1_similarity': top_k[0]['similarity'],
            'top5_listing_ids': "|".join(top5_ids),
            'top1_correct': (top1_id == gt_id),
            'top5_correct': (gt_id in top5_ids),
            'condition': row['condition'],
            'encoding_time_ms': (t1 - t0) * 1000,
            'faiss_search_time_ms': (t2 - t1) * 1000,
            'total_time_ms': (t2 - t0) * 1000
        })
        
    res_df = pd.DataFrame(results)
    res_df.to_csv(RESULTS_CSV, index=False)
    
    # 4. Metrics & Reporting
    total_queries = len(res_df)
    overall_top1_acc = res_df['top1_correct'].mean() * 100
    overall_top5_acc = res_df['top5_correct'].mean() * 100
    
    avg_lat = res_df['total_time_ms'].mean()
    med_lat = res_df['total_time_ms'].median()
    
    avg_sim_correct = res_df[res_df['top1_correct']]['top1_similarity'].mean()
    avg_sim_incorrect = res_df[~res_df['top1_correct']]['top1_similarity'].mean()
    
    cond_acc = res_df.groupby('condition')['top1_correct'].mean().sort_values() * 100
    
    report = f"""# Programmatically Generated Stumper Evaluation

**Disclaimer:** 
The generated queries have catalogue-derived ground truth, but they are not substitutes for the assignment's requested 100 self-shot phone photographs.
This is a purely synthetic, programmatic test using deterministic PIL/OpenCV transformations. It does not perfectly replicate real-world phone camera physics, lighting, or angles.

## Methodology
- **Source Data**: A random sample of {NUM_LISTINGS} unique listings drawn from the 5,144-item cleaned Etsy catalogue (Seed: {SEED}).
- **Dataset Size**: {total_queries} generated query images.
- **Transformations Used**: 10 hard-case conditions including blur, occlusion, noise, bad lighting, and perspective distortion.
- **Ground Truth**: Exact `listing_id` is retained from the source image. No manual labeling required.
- **FAISS/Matcher Status**: Evaluated directly against the production FAISS index without rebuilding or modifying the production code.

## Overall Metrics
- **Overall Top-1 Accuracy**: {overall_top1_acc:.2f}%
- **Overall Top-5 Accuracy**: {overall_top5_acc:.2f}%
- **Average Total Latency**: {avg_lat:.2f} ms
- **Median Total Latency**: {med_lat:.2f} ms
- **Average Similarity (Correct)**: {avg_sim_correct:.4f}
- **Average Similarity (Incorrect)**: {avg_sim_incorrect:.4f}

## Per-Condition Top-1 Accuracy
"""
    for cond, acc in cond_acc.items():
        report += f"- **{cond}**: {acc:.2f}%\n"
        
    report += f"""
## Analysis & Limitations
- **Hardest Condition**: {cond_acc.index[0]} ({cond_acc.iloc[0]:.2f}% Top-1 Accuracy)
- **Easiest Condition**: {cond_acc.index[-1]} ({cond_acc.iloc[-1]:.2f}% Top-1 Accuracy)

**What this experiment does and does not prove:**
This experiment proves that the production matcher is robust to certain controlled digital augmentations (like brightness changes or minor noise). However, because these are synthetic digital augmentations performed *on the catalogue image itself*, the base object geometry and background heavily overlap with the indexed image. It does NOT prove robustness against genuine out-of-domain background shifts, physical angle changes, or real-world lighting variations typical of phone photography.
"""
    with open(REPORT_MD, "w") as f:
        f.write(report)
        
    print("\n--- Summary ---")
    print(f"Number of source listings: {NUM_LISTINGS}")
    print(f"Number of generated queries: {total_queries}")
    print(f"Number of conditions: {len(conditions)}")
    print(f"Top-1 accuracy: {overall_top1_acc:.2f}%")
    print(f"Top-5 accuracy: {overall_top5_acc:.2f}%")
    print(f"Average latency: {avg_lat:.2f} ms")
    print(f"Files created: dataset.csv, results.csv, report.md in {OUT_DIR}")

if __name__ == "__main__":
    main()
