# Jhumka & Dangle Earring Error Analysis

## Overview
This report analyzes the failure modes for the 4 query images previously identified as Jhumka or dangling earrings: `test2.jpeg`, `test3.jpeg`, `test4.jpeg`, and `test8.jpeg`. The analysis uses the baseline Top-20 retrieval candidates.

## Observations
1. **The Core Item is Generally Found (but Ranked Too Low)**
   For the three true Jhumka queries (`test3`, `test4`, `test8`), the exact same item (`Listing ID: 1750297922`, "Handmade Indian Jhumki Hoop Earrings") is successfully retrieved into the Top-20 candidate pool. However, it fails to achieve Rank 1 in all three cases, settling at Rank 2, Rank 6, and Rank 2 respectively.

2. **Top-1 Irrelevance (Background/Angle Sensitivity)**
   The models' Top-1 predictions for these three images are surprisingly disparate and textually/visually incorrect for the fine-grained category:
   - `test3.jpeg` ranks a Pomegranate Watch Charm bracelet (`4510426304`) at Rank 1.
   - `test4.jpeg` ranks a Rustic pewter bee earring (`4582187140`) at Rank 1.
   - `test8.jpeg` ranks an opal huggie earring (`971657694`) at Rank 1.
   
   This indicates a **Type B failure (and Type D)**: the correct item is retrieved but ranked too low because raw zero-shot CLIP vectors are heavily biased by global image features like lighting, background textures, skin tones, or angles, rather than the fine geometric structures of the Jhumka itself.

3. **Total Failure on `test2.jpeg`**
   For `test2.jpeg` (a dangle earring), the Top-20 is completely flooded with blue gemstone earrings, but the likely correct physical item is nowhere to be seen (Type A failure). The model latched heavily onto the color/lighting rather than the specific shape.

## Diagnostic Recommendation

Based on this evidence, the model has enough capacity to pull the correct item into the broader candidate pool (Top-20), meaning the embeddings *do* encode the necessary visual similarity. However, the raw cosine-distance ranking is extremely noisy and easily distracted by cross-category items sharing similar colors or backgrounds. 

Therefore, the evidence suggests that we should **first try Option 3: Category-aware reranking** (or Option 2: Top-20 reranking). 

By implementing a filtering or re-weighting logic that restricts the Top-20 candidate pool based on a dedicated category-prediction step (e.g., heavily penalizing bracelets or pendants when the query is clearly an earring), we can instantly elevate the correct Jhumka from Rank 2 or Rank 6 up to Rank 1. This is significantly simpler and more robust than adopting a completely different embedding model (Option 4) or managing a complex multi-crop pre-processing pipeline (Option 1).
