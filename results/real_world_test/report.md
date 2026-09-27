# Real-World Exploratory Stress Test

**Disclaimer:** 
- The 4 photos used in this test (`test1.jpeg`, `test2.jpeg`, `test4.jpeg`, `test5.jpeg`) have **NO verified catalogue ground truth**. 
- These images are purely exploratory and do NOT represent the final 100-image Stumper benchmark. 
- No Top-1 accuracy is calculated, and model predictions are not labeled as "correct" or "incorrect." 
- The production FAISS index and catalogue were strictly untouched.

## Experiment Setup
- **Baseline**: Full image passed directly to the CLIP model.
- **Multi-crop**: Evaluated the full image plus 3 deterministic crops (center, upper-center, tight-center). The crop yielding the highest Top-1 inner product similarity was selected.

## Summary Statistics

### Latency (Baseline Query)
* **Average Encoding Time**: 305.82 ms
* **Average FAISS Search**: 9.13 ms
* **Average Total Latency**: 314.96 ms
* **Median Total Latency**: 275.40 ms

### Baseline vs. Multi-crop Behavior
* **Top-1 Agreement**: 1 out of 4 queries returned the exact same Top-1 listing ID.
* **Average Similarity Difference**: +0.0318 (Multi-crop vs Baseline)

## Detailed Results

### test1.jpeg
- **Baseline Top-1**: ID `4507011848` (ring) | Sim: 0.8860
- **Multicrop Top-1**: ID `4507011848` (ring) | Sim: 0.9181
- *Result remained the same.*

### test2.jpeg
- **Baseline Top-1**: ID `256613157` (earring) | Sim: 0.7902
- **Multicrop Top-1**: ID `1885800189` (earring) | Sim: 0.8235
- *Result changed due to cropping.*

### test4.jpeg
- **Baseline Top-1**: ID `4582187140` (earring) | Sim: 0.7971
- **Multicrop Top-1**: ID `1567136081` (pendant) | Sim: 0.8452
- *Result changed due to cropping.*

### test5.jpeg
- **Baseline Top-1**: ID `1737979805` (ring) | Sim: 0.8561
- **Multicrop Top-1**: ID `4503227914` (ring) | Sim: 0.8700
- *Result changed due to cropping.*

