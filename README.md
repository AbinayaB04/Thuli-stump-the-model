# Stump the Model: Visual Search Pipeline

## 1. Project Overview

This project implements a visual search pipeline that matches a photograph of jewellery against a catalogue of more than 5,000 items.

The production system uses:

```text
CLIP image encoder
        ↓
512-dimensional image embedding
        ↓
L2 normalization
        ↓
FAISS IndexFlatIP
        ↓
Top-20 retrieval
        ↓
Top-5 unique catalogue listings
        ↓
Similarity score
        ↓
Provisional open-set decision
```

The repository contains:

* the production catalogue matcher;
* the final 5,144-item catalogue metadata and FAISS index;
* experiments investigating retrieval improvements;
* an optional automated stumper experiment;
* exploratory tests using a small number of physical accessory photographs;
* evaluation reports and failure analysis.

The project deliberately distinguishes between:

* **measured results**;
* **experimental observations**; and
* **results that could not be verified because ground truth was unavailable**.

---

## 2. Assignment Coverage

### Part A — Catalogue Matcher

**Completed.**

The system:

1. acquires and cleans a jewellery catalogue;
2. generates CLIP image embeddings;
3. normalizes the embeddings;
4. stores them in a FAISS `IndexFlatIP` index;
5. retrieves the Top-20 candidates;
6. removes duplicate listing IDs;
7. returns the Top-5 unique listings;
8. reports similarity scores;
9. applies a provisional open-set decision.

The final catalogue contains **5,144 unique catalogue listings**.

### Part B — Physical / Self-Shot Stumper

**Not completed.**

The assignment requires at least 100 self-shot phone photographs of items that genuinely exist in the catalogue, with verified labels and failure-condition annotations.

That dataset was not completed.

Four physical accessory photographs were instead used for exploratory real-world testing. No verified catalogue ground truth was established for those images, so they are **not used to calculate accuracy**.

### Optional Challenge — Automated Stumper

**Completed as an additional experiment.**

A synthetic stumper generated 500 difficult query images from 50 catalogue listings using 10 controlled transformations.

This experiment provides measurable results because the ground truth is known by construction.

It **does not replace the missing 100 self-shot phone-photo requirement**.

---

## 3. Quick Start

### Requirements

* Python 3
* CPU-based PyTorch
* FAISS
* Hugging Face Transformers
* pandas
* Pillow
* the dependencies listed in `requirements.txt`

The project was developed and evaluated using CPU inference. A CUDA/NVIDIA GPU is not required.

### Installation

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The final FAISS index and metadata are already included in the repository:

```text
data/index/etsy_clip.index
data/index/etsy_index_metadata.csv
```

Therefore, the catalogue does **not** need to be re-embedded just to use or evaluate the final index.

### Running the Production Matcher

The production implementation is:

```text
src/matcher.py
```

The matcher uses the committed FAISS index and metadata and performs image encoding followed by nearest-neighbour retrieval.

The final index contains 5,144 catalogue vectors.

### Rebuilding the Catalogue

Rebuilding the catalogue from source requires downloading the catalogue images again.

The downloaded catalogue images are intentionally excluded from Git because of their size.

The committed index and metadata therefore provide the reproducible final retrieval state without requiring the evaluator to download and re-embed the full catalogue.

---

## 4. Catalogue

* **Source:** Etsy
* **Category:** Jewellery
* **Categories represented:** Rings, Earrings, Bracelets, Necklaces and Pendants
* **Final catalogue size:** **5,144 unique catalogue listings**

### Why jewellery?

Jewellery is visually challenging because it contains:

* fine geometric details;
* reflective surfaces;
* different materials and colours;
* repeated shapes;
* visually similar products.

It also provides a useful test of the difference between clean e-commerce product images and photographs taken under uncontrolled conditions.

### Catalogue acquisition and cleaning

The catalogue was collected from publicly accessible Etsy jewellery listings.

The cleaning process removed listings that were not relevant finished jewellery products, including obvious supplies and material listings.

During catalogue expansion, duplicate listing IDs were detected and removed.

The final catalogue contains:

**5,144 unique listing IDs.**

The final catalogue metadata is stored in:

```text
data/catalogue/etsy/catalogue_clean.csv
```

The original catalogue metadata is also retained at:

```text
data/catalogue/etsy/catalogue.csv
```

### Catalogue images

The downloaded catalogue images are stored locally under:

```text
data/catalogue/etsy/cleaned_images/
```

These images are excluded from Git because of their size.

The committed catalogue metadata contains the corresponding local image paths used during index construction.

---

## 5. System Architecture

```text
                  CATALOGUE PIPELINE

[Etsy Jewellery Listings]
           ↓
[Download Images + Metadata]
           ↓
[Catalogue Cleaning]
           ↓
[CLIP Image Encoder]
           ↓
[512-D Embeddings]
           ↓
[L2 Normalization]
           ↓
[FAISS IndexFlatIP]
           ↓
       Production Index


                  QUERY PIPELINE

[Query Photograph]
           ↓
[CLIP Image Encoder]
           ↓
[L2 Normalization]
           ↓
[FAISS Search]
           ↓
[Top-20 Candidates]
           ↓
[Unique Listing Filtering]
           ↓
[Top-5 Results]
           ↓
[Similarity Scores]
           ↓
[Provisional Open-Set Decision]
```

---

## 6. Retrieval Pipeline

### Model

```text
openai/clip-vit-base-patch32
```

CLIP is used as a general-purpose image encoder.

No jewellery-specific model was trained for this project.

Each image is converted into a:

```text
512-dimensional embedding
```

### Similarity

The image embeddings are L2-normalized before indexing.

The production index uses FAISS:

```text
IndexFlatIP
```

Because the vectors are normalized, inner product is equivalent to cosine similarity.

The value reported by the matcher is therefore a:

**similarity score**

It is **not a probability or calibrated confidence score**.

### Retrieval

The matcher retrieves the Top-20 nearest catalogue entries.

It then removes duplicate listing IDs and returns the Top-5 unique catalogue listings.

### Hardware

The system was evaluated using CPU-based inference.

No NVIDIA CUDA GPU was required for the final measurements.

---

## 7. Final Catalogue and Index Validation

The final production index was validated using:

```text
src/validate_final_index.py
```

Final validation results:

| Metric                           |                             Result |
| -------------------------------- | ---------------------------------: |
| Catalogue size                   |                              5,144 |
| Vectors indexed                  |                              5,144 |
| Metadata rows                    |                              5,144 |
| Unique listing IDs               |                          Confirmed |
| Embedding dimension              |                                512 |
| Vector normalization             |                           Verified |
| Metadata image paths             | Verified during index construction |
| Index build time                 |     ~1,045 seconds (~17.5 minutes) |
| Average catalogue-image encoding |                      ~201 ms/image |
| FAISS index size                 |                          ~10.05 MB |
| Metadata size                    |                           ~1.56 MB |

Exact-image self-match checks returned the corresponding catalogue item with a similarity of `1.0000`.

These checks verify index construction and lookup behaviour.

They are **not model accuracy measurements**, because the query image in those checks is identical to the indexed catalogue image.

---

## 8. Production Query Validation

The final matcher was tested using seven official query images:

```text
test1.jpeg
test2.jpeg
test3.jpeg
test4.jpeg
test5.jpeg
test6.jpeg
test8.jpeg
```

The queries were used to verify end-to-end functionality and measure CPU latency.

### CPU latency

| Measurement            |    Result |
| ---------------------- | --------: |
| Average image encoding | 278.46 ms |
| Median image encoding  | 257.69 ms |
| Average FAISS search   |   7.15 ms |
| Median FAISS search    |   2.11 ms |
| Average total latency  | 285.61 ms |

CLIP image encoding is the main latency component.

FAISS retrieval accounts for only a small portion of total query time.

### Accuracy limitation

The seven official query images do not have independently verified catalogue ground-truth labels.

Therefore:

> **No accuracy percentage is reported for these seven queries.**

Their results are used for:

* functionality validation;
* retrieval inspection;
* latency measurement; and
* qualitative error analysis.

---

## 9. Retrieval Experiments

### 9.1 Category-Aware Reranking

#### Purpose

We tested whether category-aware reranking could reduce cross-category retrieval errors.

#### Finding

Category-aware reranking reduced some cross-category noise in the tested examples.

However, it cannot recover the correct item if that item is already missing from the Top-20 candidate pool.

A wrong category prediction could also push a visually relevant item lower in the ranking.

#### Decision

The experiment was **not added as a fixed production rule**.

The experiment is retained in:

```text
src/experiment_reranking.py
results/experiments/category_reranking/
```

---

### 9.2 Multi-Crop Retrieval

#### Purpose

Real photographs may contain:

* poor framing;
* background clutter;
* partial views;
* large areas of irrelevant background.

We therefore tested the original image together with deterministic regional crops, including:

* centre crop;
* upper-centre crop;
* tighter centre crop.

#### Finding

Multi-crop retrieval changed the Top-1 result for several tested examples and increased the best similarity score for some queries.

However, the seven official queries did not have verified ground truth.

Therefore, we cannot claim that multi-crop improved overall accuracy.

#### Decision

Multi-crop remains an **experimental approach** rather than the default production matcher.

The experiment is retained in:

```text
src/experiment_multicrop.py
results/experiments/multicrop/
```

---

## 10. Open-Set Rejection

The matcher contains a provisional open-set rejection layer based on the Top-1 similarity score.

Current thresholds:

| Decision    |     Similarity |
| ----------- | -------------: |
| `MATCH`     |        >= 0.85 |
| `UNCERTAIN` | 0.78 to < 0.85 |
| `NO_MATCH`  |         < 0.78 |

### Important limitation

These thresholds are **explicitly unvalidated placeholders**.

They were not calibrated using a sufficiently large labelled dataset containing both:

* known catalogue matches; and
* known non-catalogue images.

Therefore, these values should **not** be interpreted as calibrated confidence probabilities or production-grade rejection thresholds.

A future version should calibrate them using a dedicated open-set validation dataset.

Implementation:

```text
src/rejection.py
```

Documentation:

```text
results/open_set/
```

---

## 11. Physical Photo Test

Four physical accessory photographs were used for exploratory real-world testing.

The images were run through the matcher and inspected using Top-10 candidate results and contact sheets.

### Findings

| Measurement                      |           Result |
| -------------------------------- | ---------------: |
| Verified catalogue ground truth  | None established |
| Plausible verified exact matches |                0 |
| Ambiguous cases                  |                1 |
| No-clear-match cases             |                3 |

The multi-crop experiment also showed that changing the image crop could substantially change retrieval results.

Because there is no verified ground truth for these photographs, these observations **cannot be converted into an accuracy score**.

This test should therefore be considered exploratory rather than a formal benchmark.

Related results:

```text
results/stumper/
results/real_world_test/
```

---

## 12. Automated Stumper — Optional Challenge

Because the required 100 self-shot phone-photo dataset was not completed, an automated synthetic stumper was implemented as an additional experiment.

### Methodology

| Property               | Value                                |
| ---------------------- | ------------------------------------ |
| Source listings        | 50 catalogue listings                |
| Transformations        | 10 conditions per listing            |
| Generated queries      | 500                                  |
| Ground truth           | Known by construction                |
| Catalogue              | Existing 5,144-item production index |
| Index rebuild          | Not required                         |
| Catalogue modification | None                                 |

Each synthetic query was generated from a known catalogue listing, so the expected catalogue item was known without manual labelling.

### Conditions

1. Bad lighting
2. Brightness/contrast changes
3. Blur
4. Rotation
5. Partial crop
6. Partial occlusion
7. Background clutter
8. Image noise
9. Perspective distortion
10. Combined difficult transformations

### Overall results

| Metric                             |        Result |
| ---------------------------------- | ------------: |
| Top-1 accuracy                     |    **90.40%** |
| Top-5 accuracy                     |    **95.00%** |
| Average latency in this experiment | **154.86 ms** |

The automated-stumper latency measurement uses a different evaluation setup from the production query validation in Section 8.

Therefore, the two latency values should not be directly substituted for each other.

### Per-condition Top-1 accuracy

| Condition              |   Top-1 |
| ---------------------- | ------: |
| Background clutter     |  54.00% |
| Combined difficult     |  78.00% |
| Brightness/contrast    |  90.00% |
| Partial occlusion      |  90.00% |
| Partial crop           |  94.00% |
| Image noise            |  98.00% |
| Bad lighting           | 100.00% |
| Blur                   | 100.00% |
| Perspective distortion | 100.00% |
| Rotation               | 100.00% |

These results describe the **synthetic test set only**.

They should not be interpreted as performance on real phone photographs.

The automated stumper therefore provides a controlled measurement of robustness to the implemented transformations, not a replacement for the required physical-photo benchmark.

---

## 13. Synthetic Failure Analysis

The synthetic evaluation exposed several useful failure patterns.

### Background clutter

Background clutter was the weakest synthetic condition at:

**54% Top-1 accuracy.**

The generated clutter could substantially alter the visual signal used by the model.

Some failure cases were associated with strong synthetic noise patterns.

This suggests that retrieval can be sensitive to additional visual content outside the target object.

### Partial occlusion

Heavy synthetic occlusion sometimes caused the matcher to retrieve visually dark or shadowed catalogue objects.

This indicates that when important object details are hidden, broader visual characteristics can influence retrieval more strongly.

### Brightness and contrast

Extreme brightness or contrast changes sometimes reduced visible fine details.

In those cases, the model could still identify the broad jewellery type while confusing the specific catalogue item.

### Combined transformations

Combining several transformations produced more difficult cases than many individual transformations.

These findings are observations from the synthetic dataset and should not be assumed to reproduce every failure mode of a real phone camera.

Detailed analysis:

```text
results/automated_stumper/failure_analysis.md
results/automated_stumper/failure_cases.csv
```

---

## 14. What Worked

### CLIP + FAISS

The CLIP + FAISS pipeline provided a practical end-to-end visual retrieval baseline for the 5,144-item catalogue.

### Exact FAISS Search

`IndexFlatIP` was sufficient for the current catalogue size and provided exact nearest-neighbour search without introducing the approximation trade-offs of an approximate-nearest-neighbour index.

### Controlled Synthetic Evaluation

The automated stumper provided a dataset with known ground truth, allowing accuracy to be measured without manually guessing labels.

### Failure Analysis

The synthetic experiment exposed background clutter and combined transformations as useful areas for further investigation.

### Multi-Crop Experiment

Multi-crop changed retrieval behaviour on several difficult examples and was therefore worth investigating further, although an overall accuracy improvement could not be established.

---

## 15. What Did Not Work / Limitations

### Missing Real-World Ground Truth

Accuracy could not be measured for the seven official queries because their correct catalogue listing IDs were not independently verified.

### Missing Physical Stumper Dataset

The required 100 self-shot phone photographs were not completed.

The automated stumper is therefore **not a substitute for the required physical-photo benchmark**.

### Physical Photos Had No Confirmed Matches

The four exploratory physical photographs did not provide verified catalogue ground truth.

They were therefore not used to calculate accuracy.

### Open-Set Thresholds

The rejection thresholds are provisional and have not been calibrated using a dedicated labelled open-set dataset.

### CPU Encoding Latency

CLIP encoding is the main component of query latency on the development CPU.

### Synthetic-to-Real Gap

The synthetic transformations are controlled programmatic changes.

They do not fully reproduce real camera behaviour, including:

* complex lighting;
* reflections;
* camera exposure;
* hand positioning;
* motion blur;
* real background structure.

### Catalogue Image Availability

The downloaded catalogue image files are excluded from Git because of their size.

The committed FAISS index and metadata allow the final matcher to use the existing catalogue representation without rebuilding the catalogue.

Rebuilding the index from source images requires repeating the documented catalogue acquisition and cleaning process.

---

## 16. Repository Structure

```text
thuli-stump-the-model/
│
├── README.md
├── DECISIONS.md
├── requirements.txt
│
├── data/
│   ├── catalogue/
│   │   └── etsy/
│   │       ├── catalogue.csv
│   │       ├── catalogue_clean.csv
│   │       └── final_cleaning_summary.md
│   │
│   ├── index/
│   │   ├── etsy_clip.index
│   │   ├── etsy_index_metadata.csv
│   │   └── final_index_report.md
│   │
│   ├── queries/
│   │   ├── README.md
│   │   └── images/
│   │
│   └── stumper/
│       ├── README.md
│       ├── catalogue_sampling.csv
│       ├── metadata.csv
│       └── physical_reference/
│
├── results/
│   ├── automated_stumper/
│   ├── error_analysis/
│   ├── experiments/
│   ├── final_matcher/
│   ├── open_set/
│   ├── query_review_new/
│   ├── real_world_test/
│   └── stumper/
│
└── src/
    ├── automated_evaluation.py
    ├── automated_stumper.py
    ├── build_index_final.py
    ├── experiment_multicrop.py
    ├── experiment_reranking.py
    ├── finalize_clean_catalogue.py
    ├── finalize_expansion.py
    ├── find_physical_item_matches.py
    ├── inventory_physical_photos.py
    ├── matcher.py
    ├── rejection.py
    ├── run_real_world_test.py
    ├── scraper.py
    ├── validate_final_index.py
    ├── validate_final_matcher.py
    │
    └── model/
        ├── encoder.py
        └── index.py
```

Large catalogue image directories, temporary datasets, old indices and development artefacts are excluded through `.gitignore`.

---

## 17. Reproducibility

The main production components are:

| File                              | Purpose                                 |
| --------------------------------- | --------------------------------------- |
| `src/scraper.py`                  | Catalogue acquisition                   |
| `src/finalize_clean_catalogue.py` | Catalogue cleaning                      |
| `src/finalize_expansion.py`       | Catalogue expansion/finalization        |
| `src/build_index_final.py`        | Final FAISS index construction          |
| `src/validate_final_index.py`     | Index validation                        |
| `src/matcher.py`                  | Production matcher                      |
| `src/rejection.py`                | Provisional open-set rejection          |
| `src/validate_final_matcher.py`   | Final matcher and latency validation    |
| `src/automated_stumper.py`        | Synthetic stumper generation/evaluation |
| `src/analyze_failures.py`         | Synthetic failure analysis              |
| `src/experiment_multicrop.py`     | Multi-crop experiment                   |
| `src/experiment_reranking.py`     | Category-reranking experiment           |
| `src/run_real_world_test.py`      | Physical-photo exploratory test         |

The final retrieval state is preserved in:

```text
data/index/etsy_clip.index
data/index/etsy_index_metadata.csv
```

The final catalogue metadata is preserved in:

```text
data/catalogue/etsy/catalogue_clean.csv
```

The large downloaded catalogue image dataset is intentionally excluded from Git.

API keys and deployment secrets are not included in the repository.

---

## 18. Reproducing the Reported Evaluation

The repository contains the outputs of the completed evaluations.

### Final index validation

```text
src/validate_final_index.py
```

Report:

```text
data/index/final_index_report.md
```

### Final matcher validation

```text
src/validate_final_matcher.py
```

Results:

```text
results/final_matcher/
```

### Automated stumper

```text
src/automated_stumper.py
```

Results:

```text
results/automated_stumper/
```

### Failure analysis

```text
src/analyze_failures.py
```

Results:

```text
results/automated_stumper/failure_analysis.md
```

### Multi-crop experiment

```text
src/experiment_multicrop.py
```

Results:

```text
results/experiments/multicrop/
```

### Category-reranking experiment

```text
src/experiment_reranking.py
```

Results:

```text
results/experiments/category_reranking/
```

---

## 19. Data and Reproducibility Limitations

The final catalogue images are not committed because of their size.

Consequently, a completely fresh reconstruction of the catalogue from source images requires repeating the catalogue acquisition process.

The committed FAISS index and metadata avoid this requirement for evaluation of the final retrieval state.

This distinction is intentional:

```text
Clean checkout
      ↓
Committed index + metadata
      ↓
Final retrieval state available

Rebuild from source
      ↓
Requires catalogue image acquisition
      ↓
Requires catalogue cleaning
      ↓
Requires CLIP embedding
      ↓
Requires FAISS index construction
```

---

## 20. Final Honest Assessment

The project delivers a working visual retrieval pipeline over a:

**5,144-item jewellery catalogue.**

The production matcher uses:

```text
CLIP
  ↓
L2 normalization
  ↓
FAISS IndexFlatIP
  ↓
Top-20 retrieval
  ↓
Top-5 unique listings
  ↓
Provisional open-set decision
```

On the development CPU, final matcher validation measured an average total query latency of approximately:

**285.61 ms**

with CLIP image encoding accounting for most of that time.

The controlled synthetic stumper achieved:

* **90.40% Top-1 accuracy**
* **95.00% Top-5 accuracy**

on 500 generated queries with known ground truth.

These accuracy numbers apply **only to the synthetic evaluation dataset**.

The main unresolved limitation is the absence of the required 100 self-shot phone-photo benchmark with verified catalogue labels.

Therefore, the synthetic accuracy numbers are **not presented as real-world phone-photo accuracy**.

The project also leaves the open-set thresholds explicitly uncalibrated and identifies background clutter and combined visual distortions as important areas for further investigation.

The main engineering trade-off is therefore explicit:

> **The project provides a reproducible final retrieval index and a measured synthetic robustness evaluation, but it does not claim unverified real-world accuracy.**
