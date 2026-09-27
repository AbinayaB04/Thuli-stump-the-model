import os
import pandas as pd
from pathlib import Path
from PIL import Image

from src.matcher import BaselineMatcher

QUERIES_DIR = Path("data/queries/images")
OUTPUT_DIR = Path("results/experiments/multicrop")

def get_crops(img_path):
    img = Image.open(img_path).convert('RGB')
    w, h = img.size
    
    crops = {}
    crops['original'] = img
    
    # Center crop (removing 15% margins)
    crops['center'] = img.crop((int(w*0.15), int(h*0.15), int(w*0.85), int(h*0.85)))
    
    # Upper/central object-focused crop
    crops['upper_central'] = img.crop((int(w*0.2), int(h*0.1), int(w*0.8), int(h*0.6)))
    
    # Tighter central crop
    crops['tighter_central'] = img.crop((int(w*0.3), int(h*0.3), int(w*0.7), int(h*0.7)))
    
    return crops

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading Matcher...")
    matcher = BaselineMatcher()
    
    query_files = [f for f in os.listdir(QUERIES_DIR) if f.endswith('.jpeg')]
    
    baseline_results = []
    best_crop_results = []
    max_crop_results = []
    avg_top2_results = []
    comparisons = []
    
    for q_file in query_files:
        print(f"\nProcessing {q_file}...")
        q_path = QUERIES_DIR / q_file
        
        crops = get_crops(q_path)
        
        # We need to run inference on PIL images directly.
        # But BaselineMatcher.search expects an image path. 
        # Let's save the crops temporarily.
        crop_dir = OUTPUT_DIR / f"temp_crops_{q_file}"
        crop_dir.mkdir(exist_ok=True)
        
        crop_search_results = {}
        best_crop_name = 'original'
        best_crop_top1_sim = -1
        
        for crop_name, img in crops.items():
            tmp_path = crop_dir / f"{crop_name}.jpg"
            img.save(tmp_path)
            
            matches, _, _ = matcher.search(str(tmp_path), top_k=20)
            crop_search_results[crop_name] = matches
            
            if matches and matches[0]['similarity'] > best_crop_top1_sim:
                best_crop_top1_sim = matches[0]['similarity']
                best_crop_name = crop_name
                
        # 1. Baseline
        for i, m in enumerate(crop_search_results['original'], 1):
            row = dict(m)
            row['query_image'] = q_file
            row['rank'] = i
            baseline_results.append(row)
            
        # 2. Best Crop Only
        for i, m in enumerate(crop_search_results[best_crop_name], 1):
            row = dict(m)
            row['query_image'] = q_file
            row['rank'] = i
            best_crop_results.append(row)
            
        # Aggregate across all crops
        all_candidates = {}
        for crop_name, matches in crop_search_results.items():
            for m in matches:
                lid = m['listing_id']
                if lid not in all_candidates:
                    all_candidates[lid] = {
                        'listing_id': lid,
                        'title': m['title'],
                        'category': m['category'],
                        'local_image_path': m.get('image_path', m.get('local_image_path')),
                        'similarities': []
                    }
                all_candidates[lid]['similarities'].append(m['similarity'])
                
        # 3. Max crop
        max_cands = []
        for lid, cand in all_candidates.items():
            c = dict(cand)
            c['similarity'] = max(c['similarities'])
            max_cands.append(c)
        max_cands.sort(key=lambda x: x['similarity'], reverse=True)
        
        for i, m in enumerate(max_cands[:20], 1):
            row = dict(m)
            row['query_image'] = q_file
            row['rank'] = i
            max_crop_results.append(row)
            
        # 4. Avg Top-2 crop
        avg_cands = []
        for lid, cand in all_candidates.items():
            c = dict(cand)
            sims = sorted(c['similarities'], reverse=True)
            c['similarity'] = sum(sims[:2]) / min(2, len(sims))
            avg_cands.append(c)
        avg_cands.sort(key=lambda x: x['similarity'], reverse=True)
        
        for i, m in enumerate(avg_cands[:20], 1):
            row = dict(m)
            row['query_image'] = q_file
            row['rank'] = i
            avg_top2_results.append(row)
            
        # Comparison
        b_top1 = crop_search_results['original'][0] if crop_search_results['original'] else {}
        bc_top1 = crop_search_results[best_crop_name][0] if crop_search_results[best_crop_name] else {}
        m_top1 = max_cands[0] if max_cands else {}
        a_top1 = avg_cands[0] if avg_cands else {}
        
        comparisons.append({
            'query_image': q_file,
            'baseline_top1': b_top1.get('listing_id'),
            'baseline_top1_similarity': b_top1.get('similarity'),
            'best_crop_top1': bc_top1.get('listing_id'),
            'best_crop_similarity': bc_top1.get('similarity'),
            'max_crop_top1': m_top1.get('listing_id'),
            'max_crop_similarity': m_top1.get('similarity'),
            'avg_top2_top1': a_top1.get('listing_id'),
            'avg_top2_similarity': a_top1.get('similarity')
        })

    # Save
    pd.DataFrame(baseline_results).to_csv(OUTPUT_DIR / "baseline.csv", index=False)
    pd.DataFrame(best_crop_results).to_csv(OUTPUT_DIR / "best_crop.csv", index=False)
    pd.DataFrame(max_crop_results).to_csv(OUTPUT_DIR / "max_crop.csv", index=False)
    pd.DataFrame(avg_top2_results).to_csv(OUTPUT_DIR / "avg_top2_crop.csv", index=False)
    pd.DataFrame(comparisons).to_csv(OUTPUT_DIR / "comparison.csv", index=False)
    
    print("\nJhumka Check (Listing 1750297922):")
    for q in ['test3.jpeg', 'test4.jpeg', 'test8.jpeg']:
        print(f"\n--- {q} ---")
        for name, res in [('Baseline', baseline_results), ('Best Crop', best_crop_results), 
                          ('Max Crop', max_crop_results), ('Avg Top2', avg_top2_results)]:
            df = pd.DataFrame(res)
            jhumka = df[(df['query_image'] == q) & (df['listing_id'] == 1750297922)]
            if not jhumka.empty:
                print(f"{name} Rank: {jhumka.iloc[0]['rank']}")
            else:
                print(f"{name} Rank: Not in Top 20")

if __name__ == "__main__":
    main()
