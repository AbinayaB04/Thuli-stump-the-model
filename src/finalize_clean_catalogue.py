import os
import shutil
import pandas as pd
from pathlib import Path

# Paths
DATA_DIR = Path("data/catalogue/etsy")
RAW_IMG_DIR = DATA_DIR / "images"
CLEANED_IMG_DIR = DATA_DIR / "cleaned_images"
OLD_CLEANED_IMG_DIR = DATA_DIR / "cleaned_images_old_threshold_003"
RAW_CSV = DATA_DIR / "catalogue.csv"
CLEAN_CSV = DATA_DIR / "catalogue_clean.csv"
REPORT_CSV = DATA_DIR / "cleaning_report.csv"
SUMMARY_MD = DATA_DIR / "final_cleaning_summary.md"

THRESHOLD = 0.015

def main():
    print("Loading data...")
    # 1. Load Data
    raw_df = pd.read_csv(RAW_CSV)
    report_df = pd.read_csv(REPORT_CSV)
    
    # Backup old directory if it exists and hasn't been backed up
    if CLEANED_IMG_DIR.exists() and not OLD_CLEANED_IMG_DIR.exists():
        print(f"Renaming old cleaned_images to {OLD_CLEANED_IMG_DIR.name}")
        shutil.move(str(CLEANED_IMG_DIR), str(OLD_CLEANED_IMG_DIR))
    elif CLEANED_IMG_DIR.exists():
        print("Clearing existing cleaned_images directory...")
        shutil.rmtree(CLEANED_IMG_DIR)
        
    CLEANED_IMG_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Applying new threshold rules...")
    # 2. Apply rules
    report_df['score_margin'] = pd.to_numeric(report_df['score_margin'], errors='coerce')
    
    new_decisions = []
    new_reasons = []
    
    for _, row in report_df.iterrows():
        margin = row['score_margin']
        old_reason = row['reason']
        old_decision = row['decision']
        
        # Any item without a valid margin (e.g. duplicate, too_small, missing)
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
    
    # 3. Copy accepted images and prepare clean catalogue
    print("Copying accepted images...")
    accept_ids = report_df[report_df['decision'] == 'ACCEPT']['listing_id'].astype(str).tolist()
    
    # Filter raw dataframe
    raw_df['item_id'] = raw_df['item_id'].astype(str)
    clean_df = raw_df[raw_df['item_id'].isin(accept_ids)].copy()
    
    # Dictionary for updating local_image_path
    new_paths = {}
    
    for idx, row in report_df[report_df['decision'] == 'ACCEPT'].iterrows():
        item_id = str(row['listing_id'])
        orig_path = Path(row['original_image_path'])
        
        # Ensure we are copying from the raw directory
        if not orig_path.exists():
            orig_path = RAW_IMG_DIR / f"{item_id}.jpg"
            
        dest_path = CLEANED_IMG_DIR / orig_path.name
        
        # Copy
        shutil.copy2(orig_path, dest_path)
        new_paths[item_id] = str(dest_path)
        
    # Update paths in clean catalogue
    clean_df['local_image_path'] = clean_df['item_id'].map(new_paths)
    
    # 4. Save CSVs
    print("Saving updated CSVs...")
    clean_df.to_csv(CLEAN_CSV, index=False, encoding='utf-8')
    report_df.to_csv(REPORT_CSV, index=False, encoding='utf-8')
    
    # 5. Validations
    print("Running validations...")
    total_raw = len(raw_df)
    accept_count = (report_df['decision'] == 'ACCEPT').sum()
    review_count = (report_df['decision'] == 'REVIEW').sum()
    reject_count = (report_df['decision'] == 'REJECT').sum()
    
    actual_images = len(list(CLEANED_IMG_DIR.glob("*.jpg")))
    
    assert total_raw == 4704, f"Expected 4704 raw images, got {total_raw}"
    assert accept_count + review_count + reject_count == total_raw, "Decisions don't add up to total"
    assert len(clean_df) == accept_count, "Clean CSV row count != ACCEPT count"
    assert actual_images == accept_count, "Copied images count != ACCEPT count"
    assert clean_df['item_id'].nunique() == len(clean_df), "Duplicate item_ids found in clean_df"
    
    # 6. Generate Summary
    print("Generating summary...")
    
    def get_cat_dist(df_source, condition_col, condition_val=None):
        if condition_val:
            return df_source[df_source[condition_col] == condition_val]['category'].value_counts()
        return df_source['category'].value_counts()
        
    before_cat = get_cat_dist(report_df, None)
    accept_cat = get_cat_dist(report_df, 'decision', 'ACCEPT')
    review_cat = get_cat_dist(report_df, 'decision', 'REVIEW')
    reject_cat = get_cat_dist(report_df, 'decision', 'REJECT')
    
    reasons = report_df[report_df['decision'] == 'REJECT']['reason'].value_counts()
    
    with open(SUMMARY_MD, 'w', encoding='utf-8') as f:
        f.write("# Final Cleaning Summary\n\n")
        
        f.write("## 1. Raw Dataset\n")
        f.write(f"- **Raw images**: {total_raw}\n")
        f.write(f"- **Raw listings**: {total_raw}\n\n")
        
        f.write("## 2. Final Cleaning\n")
        f.write(f"- **ACCEPT**: {accept_count} ({accept_count/total_raw*100:.1f}%)\n")
        f.write(f"- **REVIEW**: {review_count} ({review_count/total_raw*100:.1f}%)\n")
        f.write(f"- **REJECT**: {reject_count} ({reject_count/total_raw*100:.1f}%)\n\n")
        
        f.write("## 3. Category Distribution\n")
        f.write("| Category | Before | Accepted | Review | Rejected |\n")
        f.write("|----------|--------|----------|--------|----------|\n")
        for cat in before_cat.index:
            c_tot = before_cat.get(cat, 0)
            c_acc = accept_cat.get(cat, 0)
            c_rev = review_cat.get(cat, 0)
            c_rej = reject_cat.get(cat, 0)
            f.write(f"| {cat} | {c_tot} | {c_acc} | {c_rev} | {c_rej} |\n")
        f.write("\n")
            
        f.write("## 4. Rejection Reasons\n")
        for r, count in reasons.items():
            f.write(f"- **{r}**: {count}\n")
        f.write("\n")
        
        f.write("## 5. Threshold\n")
        f.write("`Selected CLIP margin threshold = 0.015`\n\n")
        f.write("This threshold was selected after:\n")
        f.write("1. Comparing multiple thresholds (0.005 to 0.030)\n")
        f.write("2. Examining category-level acceptance rates to ensure no bias against specific types of jewelry (e.g. macro ring shots)\n")
        f.write("3. Inspecting the overall CLIP score distributions\n")
        f.write("4. Visually inspecting borderline contact sheets to find the point where background noise and ambiguity become unacceptable\n\n")
        f.write("*Note: This is a selected working threshold based on the available analysis, not a mathematically perfect ground truth.*\n\n")
        
        f.write("## 6. Limitations\n")
        f.write("- CLIP scores are similarity scores, not calibrated probabilities.\n")
        f.write("- Some visually ambiguous jewelry may remain in REVIEW.\n")
        f.write("- Some difficult images may still be incorrectly accepted.\n")
        f.write("- Etsy metadata/search categories are not guaranteed ground truth.\n")
        f.write("- Further evaluation will be performed using the actual phone-photo matching task.\n")
        
    print("Done!")
    print("=" * 40)
    print("FINAL COUNTS:")
    print(f"Raw images: {total_raw}")
    print(f"ACCEPT: {accept_count}")
    print(f"REVIEW: {review_count}")
    print(f"REJECT: {reject_count}")
    print(f"Cleaned folder images: {actual_images}")
    print(f"Cleaned CSV rows: {len(clean_df)}")
    
if __name__ == "__main__":
    main()
