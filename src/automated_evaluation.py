import pandas as pd
from pathlib import Path

BASE_CSV = Path("results/experiments/multicrop/baseline.csv")
MAX_CROP_CSV = Path("results/experiments/multicrop/max_crop.csv")
OUT_CSV = Path("results/query_review_new/automated_evaluation.csv")

def main():
    df_base = pd.read_csv(BASE_CSV)
    df_mc = pd.read_csv(MAX_CROP_CSV)
    
    queries = ["test1.jpeg", "test2.jpeg", "test3.jpeg", "test4.jpeg", "test5.jpeg", "test6.jpeg", "test8.jpeg"]
    
    results = []
    
    for q in queries:
        q_mc = df_mc[df_mc['query_image'] == q].reset_index(drop=True)
        q_base = df_base[df_base['query_image'] == q].reset_index(drop=True)
        
        if q_mc.empty:
            continue
            
        # Select provisional label based on strongest strategy (max_crop Top-1)
        prov_top1 = q_mc.iloc[0]
        prov_id = prov_top1['listing_id']
        prov_cat = prov_top1['category']
        
        # Multicrop metrics
        mc_rank = prov_top1['rank']
        mc_sim = prov_top1['similarity']
        
        # Baseline metrics
        base_match = q_base[q_base['listing_id'] == prov_id]
        if not base_match.empty:
            base_rank = base_match.iloc[0]['rank']
            base_sim = base_match.iloc[0]['similarity']
        else:
            base_rank = ">20"
            base_sim = None
            
        # Agreement: Did baseline also rank this exact item as Top-1?
        base_top1_id = q_base.iloc[0]['listing_id'] if not q_base.empty else None
        agreement = "Yes" if base_top1_id == prov_id else "No"
        
        results.append({
            'query_image': q,
            'provisional_listing_id': prov_id,
            'provisional_category': prov_cat,
            'baseline_rank': base_rank,
            'baseline_similarity': f"{base_sim:.4f}" if base_sim else "N/A",
            'multicrop_rank': mc_rank,
            'multicrop_similarity': f"{mc_sim:.4f}",
            'agreement': agreement,
            'label_status': 'PSEUDO-LABEL (Model Generated)'
        })
        
    df_res = pd.DataFrame(results)
    df_res.to_csv(OUT_CSV, index=False)
    print(f"Saved {OUT_CSV}")
    
if __name__ == "__main__":
    main()
