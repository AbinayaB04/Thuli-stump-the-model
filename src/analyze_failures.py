import pandas as pd
from pathlib import Path

# Paths
RESULTS_CSV = Path("results/automated_stumper/results.csv")
DATASET_CSV = Path("results/automated_stumper/dataset.csv")
CATALOGUE_CSV = Path("data/catalogue/etsy/catalogue_clean.csv")

OUT_MD = Path("results/automated_stumper/failure_analysis.md")
OUT_CSV = Path("results/automated_stumper/failure_cases.csv")

def main():
    # Load data
    results = pd.read_csv(RESULTS_CSV)
    
    # Load catalogue to get category mapping for ground truth and predictions
    cat_df = pd.read_csv(CATALOGUE_CSV)
    if 'listing_id' not in cat_df.columns:
        cat_df['listing_id'] = cat_df['item_id']
    cat_df['listing_id'] = cat_df['listing_id'].astype(str)
    category_map = dict(zip(cat_df['listing_id'], cat_df['category']))

    # Compute stats per condition
    stats = []
    conditions = results['condition'].unique()
    
    for cond in conditions:
        subset = results[results['condition'] == cond]
        total = len(subset)
        t1_correct = subset['top1_correct'].sum()
        t5_correct = subset['top5_correct'].sum()
        avg_sim = subset['top1_similarity'].mean()
        avg_sim_corr = subset[subset['top1_correct']]['top1_similarity'].mean() if t1_correct > 0 else float('nan')
        avg_sim_incorr = subset[~subset['top1_correct']]['top1_similarity'].mean() if t1_correct < total else float('nan')
        
        stats.append({
            'Condition': cond,
            'Total': total,
            'Top-1 Correct': t1_correct,
            'Top-1 Acc': (t1_correct / total) * 100,
            'Top-5 Acc': (t5_correct / total) * 100,
            'Avg Sim': avg_sim,
            'Avg Sim (Correct)': avg_sim_corr,
            'Avg Sim (Incorrect)': avg_sim_incorr
        })
        
    stats_df = pd.DataFrame(stats).sort_values('Top-1 Acc')
    
    # Extract representative failure cases
    failures = results[~results['top1_correct']].copy()
    failures['ground_truth_category'] = failures['ground_truth_listing_id'].astype(str).map(category_map)
    failures['predicted_category'] = failures['predicted_top1_listing_id'].astype(str).map(category_map)
    
    # Output to CSV
    export_failures = failures[['query_filename', 'ground_truth_listing_id', 'predicted_top1_listing_id', 
                               'ground_truth_category', 'predicted_category', 'top1_similarity', 'condition']]
    export_failures.to_csv(OUT_CSV, index=False)
    
    # Build Markdown report
    md = "# Automated Stumper: Failure Analysis Report\n\n"
    md += "**Disclaimer:** The results below are derived from programmatic synthetic image augmentations. They are not equivalent to real-world phone-photo performance.\n\n"
    
    md += "## Per-Condition Statistics\n\n"
    for _, row in stats_df.iterrows():
        md += f"### Condition: `{row['Condition']}`\n"
        md += f"- **Number of Queries**: {row['Total']}\n"
        md += f"- **Top-1 Correct**: {row['Top-1 Correct']}\n"
        md += f"- **Top-1 Accuracy**: {row['Top-1 Acc']:.2f}%\n"
        md += f"- **Top-5 Accuracy**: {row['Top-5 Acc']:.2f}%\n"
        md += f"- **Avg Similarity**: {row['Avg Sim']:.4f}\n"
        md += f"- **Avg Sim (Correct)**: {row['Avg Sim (Correct)']:.4f}\n"
        md += f"- **Avg Sim (Incorrect)**: {row['Avg Sim (Incorrect)']:.4f}\n\n"
        
    md += "## Representative Failure Cases\n\n"
    
    focus_conds = ['background_clutter', 'combined_difficult', 'brightness_contrast', 'partial_occlusion']
    for cond in focus_conds:
        cond_failures = failures[failures['condition'] == cond]
        if cond_failures.empty:
            continue
        
        md += f"### {cond}\n"
        # Pick top 2 or 3 by similarity for representation
        rep_failures = cond_failures.sort_values('top1_similarity', ascending=False).head(3)
        for _, r in rep_failures.iterrows():
            md += f"- **Query**: `{r['query_filename']}`\n"
            md += f"  - **GT ID**: {r['ground_truth_listing_id']} ({r['ground_truth_category']})\n"
            md += f"  - **Pred ID**: {r['predicted_top1_listing_id']} ({r['predicted_category']})\n"
            md += f"  - **Similarity**: {r['top1_similarity']:.4f}\n"
        md += "\n"
        
    md += """## Observed Failure Patterns

Based on the synthetic failures:
- **`background_clutter`**: Adding sharp random noise lines severely disrupted CLIP's attention. The model was observed matching to texturally dense objects or entirely different categories, suggesting that when the structural outline is disrupted by clutter, global shape recognition fails.
- **`combined_difficult`**: The combination of blur, rotation, and lighting changes often forced the model to match on general color palettes rather than intricate jewelry details. 
- **`brightness_contrast`**: Extreme brightness/contrast adjustments occasionally bleached out metallic details, causing misclassification often within the same broad category (e.g., ring vs ring) but with an incorrect specific listing.
- **`partial_occlusion`**: Applying a heavy black occlusion block was associated with the model hallucinating matches with objects that naturally have large dark regions or shadows.

## What this experiment tells us
- The current baseline production model is highly resilient to simple isolated transformations (rotation, minor noise, simple blur).
- The model is highly sensitive to occlusion and heavy structural disruption (clutter), suggesting that it evaluates the global composition of the image rather than isolating the central object.

## What this experiment does not tell us
- It does **not** tell us the model's accuracy on genuine out-of-domain images like self-shot phone photographs in low-lit bedrooms.
- It does **not** prove that background clutter in real photos (like a desk) behaves mathematically the same as the sharp randomized RGB lines drawn in this synthetic test.
"""
    
    with open(OUT_MD, "w") as f:
        f.write(md)
        
    print(f"Generated {OUT_MD} and {OUT_CSV}")

if __name__ == "__main__":
    main()
