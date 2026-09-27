# Provisional Automated Evaluation Report

## Overview
To proceed with evaluating the ranking models without being blocked by manual ground-truth verification, this report establishes a set of **provisional pseudo-labels**. These labels are strictly model-generated references based on the strongest retrieval method (Multi-Crop Max Aggregation) and do NOT represent verified physical ground truth.

## Provisional/Model-Consistency Metrics
* **Total Queries Evaluated**: 7
* **Top-1 Agreement (Baseline vs. Multi-Crop)**: 3 out of 7 queries (42.8%)
  * The baseline and multi-crop models agreed on the Top-1 candidate for `test2`, `test3`, and `test8`.
  * They disagreed on `test1`, `test4`, `test5`, and `test6`.

## Ranking Changes (Baseline vs. Multi-Crop)
* **Queries that "Improved" (Shifted up to Rank 1 under Multi-Crop)**:
  * `test4.jpeg` (Jhumka): Baseline Rank 5 → Multi-Crop Rank 1.
  * `test5.jpeg`: Baseline Rank 17 → Multi-Crop Rank 1.
  * `test6.jpeg`: Baseline Rank 15 → Multi-Crop Rank 1.
  * `test1.jpeg`: Baseline Rank 2 → Multi-Crop Rank 1.
* **Queries that Remained Difficult (Retrieval Failures)**:
  * `test2.jpeg`: Both Baseline and Multi-Crop strongly agree on an incorrect cluster of blue gemstone earrings (Rank 1 match). This indicates a fundamental embedding failure (color bias overpowering shape) rather than a simple ranking issue.
  * `test3.jpeg`: Multi-crop continues to heavily favor an incorrect bracelet charm at Rank 1.

## Jhumka-Specific Observations
Using the strongest Multi-Crop candidate as the provisional label successfully targets the correct Jhumka geometry for `test4` and `test8`. 
* The likely Jhumka (`Listing ID: 1750297922`) was successfully selected as the provisional Top-1 target for both `test4` and `test8`.
* The multi-crop strategy was demonstrably responsible for pulling this candidate up from Rank 5 in the baseline all the way to Rank 1 for `test4`.

## Limitations of Pseudo-Labels
1. **Model Bias Confirmation**: By defining the "ground truth" as the model's own strongest prediction, any fundamental failures in the embedding space (such as the color bias on `test2.jpeg`) will be falsely reported as a "success" (Rank 1 match) in automated evaluation scripts.
2. **Not Physical Ground Truth**: Pseudo-labels are inherently speculative. A candidate might look visually identical in a thumbnail but differ in physical scale, material, or listing details. 
3. **Usage Constraint**: These metrics are strictly designed for testing ranking *consistency* and *stability* between pipeline iterations. They cannot and must not be presented as true real-world retrieval accuracy.
