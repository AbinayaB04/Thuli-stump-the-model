import os
import math
import numpy as np
import pandas as pd
import faiss
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from src.model.encoder import ImageEncoder

# Paths
REFERENCE_DIR = Path("data/stumper/physical_reference")
INDEX_DIR = Path("data/index")
INDEX_PATH = INDEX_DIR / "etsy_clip.index"
METADATA_PATH = INDEX_DIR / "etsy_index_metadata.csv"

RESULTS_DIR = Path("results/stumper")
CSV_OUT = RESULTS_DIR / "physical_item_candidates.csv"
CONTACT_SHEET_DIR = RESULTS_DIR / "physical_candidates"

def ensure_unique_top_k(D, I, metadata_df, k=10):
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

def create_contact_sheet(ref_path, top_candidates, out_path):
    # Reference image + 10 candidates = 11 images
    # Let's do a grid of 3 rows x 4 cols (12 slots)
    fig, axes = plt.subplots(3, 4, figsize=(16, 12))
    axes = axes.flatten()
    
    # 1. Reference Photo
    try:
        ref_img = Image.open(ref_path).convert("RGB")
        axes[0].imshow(ref_img)
        axes[0].set_title(f"REFERENCE:\n{ref_path.name}")
    except Exception as e:
        axes[0].set_title(f"Error loading ref\n{e}")
    axes[0].axis('off')
    
    # 2. Top-10 Candidates
    for i, cand in enumerate(top_candidates):
        ax = axes[i + 1]
        try:
            cand_img = Image.open(cand['image_path']).convert("RGB")
            ax.imshow(cand_img)
            
            title_text = f"Rank {i+1} | ID: {cand['listing_id']}\nSim: {cand['similarity']:.4f}\n{cand['category']}"
            ax.set_title(title_text, fontsize=10)
        except Exception as e:
            ax.set_title(f"Error loading cand\n{e}", fontsize=10)
        ax.axis('off')
        
    # Hide any unused axes
    for j in range(len(top_candidates) + 1, len(axes)):
        axes[j].axis('off')
        
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def main():
    print("Preparing Physical Item Matching Workflow...")
    
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CONTACT_SHEET_DIR.mkdir(parents=True, exist_ok=True)
    
    reference_images = [f for f in REFERENCE_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    if not reference_images:
        print(f"No reference images found in {REFERENCE_DIR}")
        print(f"Please add your physical item photos there and run again.")
        
        # Initialize an empty CSV to avoid errors down the line if users expect it
        pd.DataFrame(columns=[
            'reference_image', 'rank', 'listing_id', 'category', 'title', 'similarity', 'catalogue_image_path'
        ]).to_csv(CSV_OUT, index=False)
        return
        
    print("Loading final FAISS index and metadata...")
    index = faiss.read_index(str(INDEX_PATH))
    metadata_df = pd.read_csv(METADATA_PATH)
    
    encoder = ImageEncoder()
    
    all_results = []
    
    for ref_path in reference_images:
        print(f"\nProcessing {ref_path.name}...")
        q_emb = encoder.encode(str(ref_path))
        
        if q_emb is None:
            print(f"Failed to encode {ref_path.name}")
            continue
            
        faiss.normalize_L2(q_emb)
        
        # Search Top-30 to ensure we get 10 unique
        D, I = index.search(q_emb, k=30)
        top10 = ensure_unique_top_k(D[0], I[0], metadata_df, k=10)
        
        # Build CSV rows
        for rank, match in enumerate(top10, 1):
            all_results.append({
                'reference_image': ref_path.name,
                'rank': rank,
                'listing_id': match['listing_id'],
                'category': match['category'],
                'title': match['title'],
                'similarity': match['similarity'],
                'catalogue_image_path': match['image_path']
            })
            
        # Create Contact Sheet
        out_sheet_path = CONTACT_SHEET_DIR / f"{ref_path.stem}_candidates.jpg"
        create_contact_sheet(ref_path, top10, out_sheet_path)
        print(f"  -> Saved contact sheet to {out_sheet_path}")
        
    # Save CSV
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df.to_csv(CSV_OUT, index=False)
        print(f"\nSaved Top-10 candidates for all references to {CSV_OUT}")
    else:
        print("\nNo valid results generated.")
        
    print("\nDone! Please review the contact sheets manually to confirm exact matches.")

if __name__ == "__main__":
    main()
