# Final Cleaning Summary

## 1. Raw Dataset
- **Raw images**: 4704
- **Raw listings**: 4704

## 2. Final Cleaning
- **ACCEPT**: 3977 (84.5%)
- **REVIEW**: 532 (11.3%)
- **REJECT**: 195 (4.1%)

## 3. Category Distribution
| Category | Before | Accepted | Review | Rejected |
|----------|--------|----------|--------|----------|
| ring | 1032 | 854 | 125 | 53 |
| earring | 1000 | 836 | 136 | 28 |
| bracelet | 1000 | 853 | 113 | 34 |
| necklace | 1000 | 856 | 94 | 50 |
| pendant | 672 | 578 | 64 | 30 |

## 4. Rejection Reasons
- **clip_non_jewelry**: 154
- **too_bright**: 33
- **duplicate_image**: 5
- **too_dark**: 3

## 5. Threshold
`Selected CLIP margin threshold = 0.015`

This threshold was selected after:
1. Comparing multiple thresholds (0.005 to 0.030)
2. Examining category-level acceptance rates to ensure no bias against specific types of jewelry (e.g. macro ring shots)
3. Inspecting the overall CLIP score distributions
4. Visually inspecting borderline contact sheets to find the point where background noise and ambiguity become unacceptable

*Note: This is a selected working threshold based on the available analysis, not a mathematically perfect ground truth.*

## 6. Limitations
- CLIP scores are similarity scores, not calibrated probabilities.
- Some visually ambiguous jewelry may remain in REVIEW.
- Some difficult images may still be incorrectly accepted.
- Etsy metadata/search categories are not guaranteed ground truth.
- Further evaluation will be performed using the actual phone-photo matching task.
