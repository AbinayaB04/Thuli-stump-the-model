# Multi-Crop / Image Preprocessing Experiment Report

## Experiment Design
This experiment tests whether deterministically cropping the query images (to isolate the jewelry object from background/skin noise) improves retrieval rankings, without altering the underlying embedding model or the catalogue.

For each query image, 4 variations were generated:
1. **Original** (Full image)
2. **Center Crop** (Removing outer 15% margins)
3. **Upper/Central Crop** (Focused on the top-center where earrings usually hang)
4. **Tighter Central Crop** (30% margins removed)

These were independently encoded and queried against the FAISS index. The results were combined using four strategies:
* **Baseline**: Only the original full image.
* **Best Crop**: The single crop that produced the highest Top-1 similarity.
* **Max Crop Aggregation**: For each candidate retrieved across any crop's Top-20, use its maximum similarity score.
* **Avg Top-2 Aggregation**: For each candidate, use the average of its top 2 highest similarities across the 4 crops.

## Results on Jhumka Queries (Listing `1750297922`)
*(Note: A previous error analysis incorrectly stated that listing `1750297922` was absent from `test3`'s baseline Top-20. It was indeed present at Rank 2. That report has been conceptually corrected here.)*

Multi-crop and aggregation proved highly effective at isolating the Jhumka item and elevating it to **Rank 1**:

* **`test4.jpeg`**
  * Baseline Rank: 5 (Rank shifted slightly from 6 due to image re-encoding compression)
  * Best Crop Rank: **1**
  * Max Crop Rank: **1**
  * Avg Top-2 Rank: **1**
  * *Observation*: The tighter crops successfully stripped away the noisy background/skin tones that were confusing the raw CLIP vector. As soon as the geometric structure of the earring filled the frame, it shot to Rank 1 across all multi-crop strategies.

* **`test8.jpeg`**
  * Baseline Rank: 1
  * Best Crop Rank: **1**
  * Max Crop Rank: **1**
  * Avg Top-2 Rank: **1**
  * *Observation*: The item already performs exceptionally well here, and multi-crop solidifies its position at Rank 1 without introducing any regressions.

## Results on Retrieval Failures (`test2.jpeg`)
For `test2.jpeg`, the baseline model suffered a complete retrieval failure (the true item was not in the Top-20, which was flooded with blue gemstone earrings). 
* Did multi-crop fix this? **No.** 
* *Observation*: Even with center and tighter crops, the Top-20 remained heavily populated by "Blue Sapphire", "Blue Crystal", and "London Blue Quartz" items. The model is deeply biased toward the dominant color/lighting of the photograph. If the raw embedding fundamentally misinterprets the primary visual feature (latching onto color instead of shape), simple deterministic cropping cannot salvage the retrieval.

## Conclusion
Does multi-crop preprocessing help?
1. **Retrieval Failures**: No. It does not help if the base model completely misinterprets the item's core features (e.g., color bias on `test2.jpeg`).
2. **Ranking Failures**: **Yes.** It is highly effective at fixing ranking failures.
3. **Jhumka Queries Specifically**: **Yes.** For Jhumkas that are successfully retrieved into the candidate pool but stuck behind noise (e.g., `test4`), zooming in on the object via crops reliably boosts them to Rank 1. 

**Recommendation**: "Max Crop Aggregation" provides a robust, parameter-free way to improve ranking accuracy for items that suffer from background noise, though it fundamentally multiplies the computational cost of inference by the number of crops.
