import os
import pandas as pd
from PIL import Image
from pathlib import Path

REF_DIR = Path("data/stumper/physical_reference")
CANDIDATES_CSV = Path("results/stumper/physical_item_candidates.csv")
INVENTORY_CSV = Path("results/stumper/physical_photo_inventory.csv")

def main():
    print("Generating Physical Photo Inventory...")
    
    if not REF_DIR.exists():
        print(f"Directory {REF_DIR} does not exist.")
        return
        
    photos = [p for p in REF_DIR.iterdir() if p.is_file() and p.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    total_photos = len(photos)
    unique_names = len(set([p.name for p in photos]))
    
    if total_photos == 0:
        print("No photos found.")
        return
        
    # Read candidates to merge with image info
    cand_df = pd.DataFrame()
    if CANDIDATES_CSV.exists():
        cand_df = pd.read_csv(CANDIDATES_CSV)
        
    inventory = []
    strong_candidates = 0
    difficult_candidates = 0
    
    STRONG_SIM_THRESHOLD = 0.82
    
    for photo in photos:
        try:
            with Image.open(photo) as img:
                width, height = img.size
                file_type = img.format
        except Exception:
            width, height, file_type = 0, 0, "UNKNOWN"
            
        # Get top candidates for this photo
        top1_id = ""
        top1_cat = ""
        top1_sim = 0.0
        top5_ids = ""
        
        if not cand_df.empty:
            photo_cands = cand_df[cand_df['reference_image'] == photo.name].sort_values('rank')
            if not photo_cands.empty:
                top1_row = photo_cands.iloc[0]
                top1_id = top1_row['listing_id']
                top1_cat = top1_row['category']
                top1_sim = float(top1_row['similarity'])
                
                # Get Top 5 IDs
                top5 = photo_cands.head(5)
                top5_ids = "|".join([str(x) for x in top5['listing_id'].tolist()])
                
                if top1_sim >= STRONG_SIM_THRESHOLD:
                    strong_candidates += 1
                else:
                    difficult_candidates += 1
            else:
                difficult_candidates += 1
        else:
            difficult_candidates += 1
            
        inventory.append({
            'filename': photo.name,
            'width': width,
            'height': height,
            'file_type': file_type,
            'top1_listing_id': top1_id,
            'top1_category': top1_cat,
            'top1_similarity': top1_sim,
            'top5_listing_ids': top5_ids
        })
        
    # Save inventory
    inv_df = pd.DataFrame(inventory)
    inv_df.to_csv(INVENTORY_CSV, index=False)
    
    print("\n--- Physical Photo Inventory ---")
    print(f"Total number of existing real photos: {total_photos}")
    print(f"Number of unique filenames: {unique_names}")
    print(f"Number of photos with a strong catalogue candidate (sim >= {STRONG_SIM_THRESHOLD}): {strong_candidates}")
    print(f"Number of photos that appear difficult/ambiguous (sim < {STRONG_SIM_THRESHOLD}): {difficult_candidates}")
    print(f"\nInventory saved to {INVENTORY_CSV}")
    print("\nNote: Do NOT assume any Top-1 result is a guaranteed exact physical match. This is purely visual mapping assistance.")

if __name__ == "__main__":
    main()
