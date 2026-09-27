# Evaluation Summary

This document provides a concise metrics summary of the Stump the Model visual search pipeline.

### Catalogue / Index
| Metric | Value | Status |
|---|---|---|
| Final Unique Catalogue Size | 5,144 | Verified / Measured |
| FAISS Vectors Indexed | 5,144 | Verified / Measured |
| Vector Dimensionality | 512 | Verified / Measured |
| Index Build Time | ~1,045 ms | Measured |
| Average Build Encoding Time | ~201 ms/image | Measured |

### Query Latency (Final Matcher)
*Based on the 7 original official queries running on CPU.*

| Metric | Value | Status |
|---|---|---|
| Average Total Latency | 285.61 ms | Measured |
| Average Image Encoding | 278.46 ms | Measured |
| Median Image Encoding | 257.69 ms | Measured |
| Average FAISS Search | 7.15 ms | Measured |
| Median FAISS Search | 2.11 ms | Measured |

*(Note: The 7 original query images do not have verified accuracy due to missing ground truth.)*

### Physical Photo Evaluation (Stumper Requirement)
An exploratory test using 4 genuine physical accessory photographs.

| Metric | Value | Status |
|---|---|---|
| Clearly Plausible Verified Matches | 0 | Unverified (Missing Ground Truth) |
| Ambiguous Candidates | 1 | Unverified (Missing Ground Truth) |
| No-Clear-Match Cases | 3 | Unverified (Missing Ground Truth) |

*(Note: No accuracy claims are made for physical photos, as verified ground truth was unavailable.)*

### Automated Stumper (Optional Challenge)
A programmatic evaluation using 500 synthetically augmented query images derived from the 5,144-item catalogue.

| Metric | Value | Status |
|---|---|---|
| Dataset Size | 500 queries | Synthetic Evaluation |
| Overall Top-1 Accuracy | 90.40% | Synthetic Evaluation |
| Overall Top-5 Accuracy | 95.00% | Synthetic Evaluation |
| Average Total Latency | 154.86 ms | Measured |

**Per-Condition Top-1 Accuracy (Synthetic Evaluation):**
- background_clutter: 54.00%
- combined_difficult: 78.00%
- brightness_contrast: 90.00%
- partial_occlusion: 90.00%
- partial_crop: 94.00%
- image_noise: 98.00%
- bad_lighting: 100.00%
- blur: 100.00%
- perspective_distortion: 100.00%
- rotation: 100.00%

### Failure Analysis
Based on the synthetic Automated Stumper evaluation:
- **Primary Failure Mode**: Severe structural disruption (e.g., sharp random line clutter) severely degraded the model's global shape recognition.
- **Secondary Failure Mode**: Heavy occlusion caused the model to hallucinate matches with items containing naturally dark regions or shadows.

### Open-set Rejection

| Threshold | Provisional Value | Status |
|---|---|---|
| `MATCH` | >= 0.85 | Provisional / Unvalidated |
| `UNCERTAIN` | 0.78 to < 0.85 | Provisional / Unvalidated |
| `NO_MATCH` | < 0.78 | Provisional / Unvalidated |

*(Note: These values are strictly architectural placeholders and have not been scientifically calibrated against a verified dataset.)*
