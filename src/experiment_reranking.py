import os
import pandas as pd
from pathlib import Path

INPUT_DIR = Path("results/query_review_new")
OUTPUT_DIR = Path("results/experiments/category_reranking")

KNOWN_CATEGORIES = {
    "test1.jpeg": "ring",
    "test2.jpeg": "earring",
    "test3.jpeg": "earring",
    "test4.jpeg": "earring",
    "test5.jpeg": "bracelet",  # original 'bangle'
    "test6.jpeg": "bracelet",
    "test8.jpeg": "earring"
}

PENALTIES = {
    "baseline": 0.0,
    "mild": -0.05,
    "medium": -0.15
}

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    query_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv') and f.startswith('test')]
    
    all_results = {p: [] for p in PENALTIES}
    comparisons = []
    
    for q_csv in query_files:
        q_image = q_csv.replace('.csv', '.jpeg')
        if q_image not in KNOWN_CATEGORIES:
            continue
            
        expected_cat = KNOWN_CATEGORIES[q_image]
        df = pd.read_csv(INPUT_DIR / q_csv)
        
        comp_row = {'query_image': q_image, 'expected_category': expected_cat}
        
        for p_name, p_val in PENALTIES.items():
            # Calculate rerank score
            df_exp = df.copy()
            
            # Apply penalty if category mismatch
            df_exp['rerank_score'] = df_exp.apply(
                lambda row: row['similarity'] if str(row['category']).lower() == expected_cat else row['similarity'] + p_val,
                axis=1
            )
            
            # Re-sort by rerank_score desc
            df_exp = df_exp.sort_values(by=['rerank_score', 'similarity'], ascending=[False, False]).reset_index(drop=True)
            
            # Re-assign rank
            df_exp['rank'] = df_exp.index + 1
            df_exp['query_image'] = q_image
            
            # Select columns
            df_out = df_exp[['query_image', 'rank', 'listing_id', 'title', 'category', 'similarity', 'rerank_score']]
            all_results[p_name].extend(df_out.to_dict('records'))
            
            # Record for comparison
            comp_row[f'{p_name}_top1'] = str(df_exp.iloc[0]['listing_id'])
            comp_row[f'{p_name}_top5'] = ",".join(df_exp.head(5)['listing_id'].astype(str).tolist())
            
        comparisons.append(comp_row)
        
    # Save per-penalty CSVs
    for p_name, rows in all_results.items():
        pd.DataFrame(rows).to_csv(OUTPUT_DIR / f"{p_name}.csv", index=False)
        print(f"Saved {OUTPUT_DIR / f'{p_name}.csv'}")
        
    # Save comparison CSV
    pd.DataFrame(comparisons).to_csv(OUTPUT_DIR / "comparison.csv", index=False)
    print(f"Saved {OUTPUT_DIR / 'comparison.csv'}")
    
    # Quick terminal output for jhumka
    print("\nJhumka Candidate (1750297922) Rankings:")
    for p_name, rows in all_results.items():
        print(f"\n--- {p_name.upper()} ---")
        df_p = pd.DataFrame(rows)
        jhumka = df_p[df_p['listing_id'] == 1750297922]
        if not jhumka.empty:
            for _, r in jhumka.iterrows():
                print(f"{r['query_image']}: Rank {r['rank']} (Score: {r['rerank_score']:.4f})")
                
if __name__ == "__main__":
    main()
