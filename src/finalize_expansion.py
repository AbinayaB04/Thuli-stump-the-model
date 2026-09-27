import os
import shutil
import pandas as pd
from pathlib import Path

# Paths
DATA_DIR = Path("data/catalogue/etsy/expansion_raw")
EXPANSION_CLEAN_DIR = Path("data/catalogue/etsy/expansion_clean")

RAW_IMG_DIR = DATA_DIR / "images"
CLEANED_IMG_DIR = EXPANSION_CLEAN_DIR / "cleaned_images"
RAW_CSV = DATA_DIR / "catalogue.csv"
CLEAN_CSV = EXPANSION_CLEAN_DIR / "catalogue_clean.csv"
REPORT_CSV = EXPANSION_CLEAN_DIR / "cleaning_report.csv"

THRESHOLD = 0.015

def main():
    print("Loading data...")
    raw_df = pd.read_csv(RAW_CSV)
    report_df = pd.read_csv(REPORT_CSV)
    
    if CLEANED_IMG_DIR.exists():
        print("Clearing existing cleaned_images directory...")
        shutil.rmtree(CLEANED_IMG_DIR)
        
    CLEANED_IMG_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Applying new threshold rules...")
    report_df['score_margin'] = pd.to_numeric(report_df['score_margin'], errors='coerce')
    
    new_decisions = []
    new_reasons = []
    
    for _, row in report_df.iterrows():
        margin = row['score_margin']
        old_reason = row['reason']
        old_decision = row['decision']
        
        if pd.isna(margin):
            new_decisions.append('REJECT')
            new_reasons.append(old_reason)
        else:
            if margin >= THRESHOLD:
                new_decisions.append('ACCEPT')
                new_reasons.append('clip_jewelry')
            elif margin >= 0.000:
                new_decisions.append('REVIEW')
                new_reasons.append('clip_uncertain')
            else:
                new_decisions.append('REJECT')
                new_reasons.append('clip_non_jewelry')
                
    report_df['decision'] = new_decisions
    report_df['reason'] = new_reasons
    
    print("Copying accepted images...")
    accept_ids = report_df[report_df['decision'] == 'ACCEPT']['listing_id'].astype(str).tolist()
    
    raw_df['item_id'] = raw_df['item_id'].astype(str)
    
    clean_df = raw_df[raw_df['item_id'].isin(accept_ids)].copy()
    
    new_paths = {}
    
    for idx, row in report_df[report_df['decision'] == 'ACCEPT'].iterrows():
        item_id = str(row['listing_id'])
        orig_path = Path(row['original_image_path'])
        
        if not orig_path.exists():
            orig_path = RAW_IMG_DIR / f"etsy_{item_id}.jpg"
            if not orig_path.exists():
                orig_path = RAW_IMG_DIR / f"{item_id}.jpg"
            
        dest_path = CLEANED_IMG_DIR / orig_path.name
        
        try:
            shutil.copy2(orig_path, dest_path)
            new_paths[item_id] = str(dest_path)
        except:
            pass
            
    # Update paths in clean catalogue
    clean_df['local_image_path'] = clean_df['item_id'].map(new_paths)
    
    print("Saving updated CSVs...")
    clean_df.to_csv(CLEAN_CSV, index=False, encoding='utf-8')
    report_df.to_csv(REPORT_CSV, index=False, encoding='utf-8')
    
    print("Done!")
    
    total_raw = len(raw_df)
    accept_count = (report_df['decision'] == 'ACCEPT').sum()
    print(f"Raw images: {total_raw}")
    print(f"ACCEPT: {accept_count}")
    print(f"Cleaned folder images: {len(list(CLEANED_IMG_DIR.glob('*.jpg')))}")
    print(f"Cleaned CSV rows: {len(clean_df)}")
    
if __name__ == "__main__":
    main()
