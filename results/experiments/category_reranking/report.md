# Category Reranking Experiment Report

## Experiment Design
This controlled experiment evaluates whether penalizing candidates that do not match the expected fine-grained category improves retrieval rankings for known hard queries (like Jhumkas).

**Methodology**:
* Base predictions are drawn strictly from the existing Top-20 retrieval candidates (`results/query_review_new/`).
* Three penalty values were tested:
  * **Baseline**: 0.0 penalty
  * **Mild**: -0.05 applied to `clip_similarity` if category mismatches.
  * **Medium**: -0.15 applied to `clip_similarity` if category mismatches.
* The query category is assumed strictly from the previously known ground-truth context (e.g., `test4.jpeg` = `earring`).
* All candidates were then re-sorted by their new `rerank_score`.

## Penalty Values Tested
* **baseline.csv** (`penalty = 0.0`)
* **mild.csv** (`penalty = -0.05`)
* **medium.csv** (`penalty = -0.15`)

## Results & Jhumka-Specific Observations
The category reranking successfully pushes out-of-category candidates down, but reveals a critical limitation when dealing with intra-category visual distractors.

**Case Study: Jhumka Candidate (ID: 1750297922)**
* **test4.jpeg (Query: Earring)**: 
  * Baseline Rank: 6
  * Mild/Medium Rank: 3
  * *Observation*: The Jhumka successfully jumped from Rank 6 to Rank 3 because the baseline ranks 2, 3, and 5 were actually a pendant, a bracelet, and a necklace. The reranker penalized those, allowing the correct earring to rise. However, it hit a ceiling at Rank 3 because Ranks 1 and 4 were *also earrings* (e.g., a pewter bee earring) that had slightly higher raw CLIP similarities.
* **test8.jpeg (Query: Earring)**:
  * Baseline Rank: 2
  * Mild/Medium Rank: 2
  * *Observation*: The Jhumka was stuck at Rank 2. The item at Rank 1 (an opal huggie) is also an earring. Since category reranking applies a flat penalty to out-of-category items, it cannot differentiate between a "huggie earring" and a "jhumka earring" if both are labeled simply as `earring` in the catalogue.

## Regressions
Category reranking relies entirely on the accuracy of the catalogue metadata. For example, in `test3.jpeg`, the baseline Top-1 was a bracelet charm. When the penalty was applied (because `test3` is an earring), the bracelet charm correctly plummeted from Rank 1 to Rank 3. But since the correct Jhumka was not even in the Top-20 for `test3`, the new Rank 1 simply became a random generic silver earring.

There were no massive regressions for non-Jhumka queries since the penalty behaves predictably, but it can artificially boost irrelevant items simply because they have the correct categorical tag.

## Limitations
1. **Intra-Category Confusion**: A category penalty only filters out massive errors (e.g., a bracelet appearing in an earring search). It does *not* help distinguish a Jhumka earring from a Stud earring, because both share the same category tag.
2. **Missing from Top-20**: Reranking can only re-sort candidates that are already present in the candidate pool. If the item failed to make the Top-20 entirely (like `test2.jpeg` or `test3.jpeg` for the target Jhumka), reranking is powerless to fix it.
3. **Reliance on Perfect Metadata**: If an item in the catalogue was mislabeled, it would be unfairly penalized by the reranker.

## Conclusion
Category-aware reranking provides a measurable but limited improvement. It clears out obvious cross-category noise (pushing the Jhumka in `test4` from Rank 6 to Rank 3). However, to fully solve the Jhumka queries and push them to Rank 1, we would need either:
1. Deeper metadata (sub-categories like `jhumka` vs `stud`).
2. A more robust embedding model or multi-crop preprocessing that isolates the actual item geometry from the noisy background/lighting.
