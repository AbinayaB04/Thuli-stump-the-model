# Programmatically Generated Stumper Evaluation

**Disclaimer:** 
The generated queries have catalogue-derived ground truth, but they are not substitutes for the assignment's requested 100 self-shot phone photographs.
This is a purely synthetic, programmatic test using deterministic PIL/OpenCV transformations. It does not perfectly replicate real-world phone camera physics, lighting, or angles.

## Methodology
- **Source Data**: A random sample of 50 unique listings drawn from the 5,144-item cleaned Etsy catalogue (Seed: 42).
- **Dataset Size**: 500 generated query images.
- **Transformations Used**: 10 hard-case conditions including blur, occlusion, noise, bad lighting, and perspective distortion.
- **Ground Truth**: Exact `listing_id` is retained from the source image. No manual labeling required.
- **FAISS/Matcher Status**: Evaluated directly against the production FAISS index without rebuilding or modifying the production code.

## Overall Metrics
- **Overall Top-1 Accuracy**: 90.40%
- **Overall Top-5 Accuracy**: 95.00%
- **Average Total Latency**: 154.86 ms
- **Median Total Latency**: 152.33 ms
- **Average Similarity (Correct)**: 0.9169
- **Average Similarity (Incorrect)**: 0.8110

## Per-Condition Top-1 Accuracy
- **background_clutter**: 54.00%
- **combined_difficult**: 78.00%
- **brightness_contrast**: 90.00%
- **partial_occlusion**: 90.00%
- **partial_crop**: 94.00%
- **image_noise**: 98.00%
- **bad_lighting**: 100.00%
- **blur**: 100.00%
- **perspective_distortion**: 100.00%
- **rotation**: 100.00%

## Analysis & Limitations
- **Hardest Condition**: background_clutter (54.00% Top-1 Accuracy)
- **Easiest Condition**: rotation (100.00% Top-1 Accuracy)

**What this experiment does and does not prove:**
This experiment proves that the production matcher is robust to certain controlled digital augmentations (like brightness changes or minor noise). However, because these are synthetic digital augmentations performed *on the catalogue image itself*, the base object geometry and background heavily overlap with the indexed image. It does NOT prove robustness against genuine out-of-domain background shifts, physical angle changes, or real-world lighting variations typical of phone photography.
