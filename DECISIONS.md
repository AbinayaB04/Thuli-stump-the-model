# Engineering Decisions

This document explains the main implementation choices made while building the visual search pipeline and why some approaches were kept as experiments rather than used in the final system.

## 1. Why Etsy Jewellery?

We chose jewellery because it is visually challenging for image matching. Jewellery contains fine shapes, small details, reflective surfaces and different materials. These properties can look very different under changes in lighting, angle and background.

Jewellery also matches the preferred catalogue categories for the assignment, such as rings, earrings, bracelets and necklaces.

The catalogue was collected from Etsy and cleaned to obtain **5,144 unique catalogue listings**.

## 2. Why CLIP?

We used `openai/clip-vit-base-patch32` as the image encoder.

CLIP provides general-purpose visual embeddings without requiring us to train a jewellery-specific model from scratch. This made it suitable for building an initial image-retrieval system with limited labelled training data.

The model converts each image into a **512-dimensional embedding**. These embeddings are then normalized before being stored in the FAISS index.

## 3. Why FAISS?

We needed a vector search library that could efficiently search the CLIP embeddings.

FAISS provides a simple and efficient implementation for nearest-neighbour search. It also gives us the option to replace the exact index with an approximate-nearest-neighbour index later if the catalogue becomes much larger.

For the current catalogue of 5,144 items, exact search was practical, so we did not need an approximate index.

## 4. Why IndexFlatIP?

We used `IndexFlatIP`.

`IndexFlatIP` performs an exact inner-product search over the stored vectors. It does not use an approximate search structure, so it does not introduce an approximation error.

Since the catalogue contains only 5,144 items, searching all vectors is fast enough for the current system.

The final production index contains:

* 5,144 vectors
* 512 dimensions per vector
* L2-normalized embeddings
* Exact inner-product search

The measured average FAISS search time during final matcher validation was approximately **7 ms** on the development machine.

## 5. Why Cosine Similarity?

The CLIP embeddings are L2-normalized before indexing.

For two normalized vectors, their inner product is equivalent to cosine similarity:

`cosine similarity = normalized vector · normalized vector`

Therefore, using `IndexFlatIP` on the normalized CLIP embeddings gives us cosine-similarity-based retrieval.

The score reported by the matcher is therefore a **similarity score**, not a calibrated probability or confidence value.

## 6. Why Top-20 → Top-5 Unique Listings?

The matcher first retrieves the top 20 nearest catalogue entries.

We then remove duplicate listing IDs and return the top 5 unique listings.

This gives the system a larger candidate pool while preventing the final Top-5 result from being dominated by repeated entries associated with the same listing.

The final output contains the catalogue listing ID, category/title information and similarity score.

## 7. Why Was Multi-Crop Investigated?

Phone photographs can contain background clutter, poor framing or partial views of an object.

We therefore tested a multi-crop approach using the original image together with selected crops. The experiment checked whether focusing on different regions could change retrieval behaviour.

The experiment changed some predictions and produced useful improvements on individual difficult examples. However, we did not have verified ground truth for the seven official query images, so we did **not** claim an overall accuracy improvement from multi-crop.

The final production matcher therefore remains the simpler full-image retrieval pipeline.

## 8. Why Was Category Reranking Kept as an Experiment?

Category-aware reranking was tested as a separate experiment.

It reduced some cross-category mismatches. For example, applying a category penalty could move an item from another jewellery category lower in the results.

However, a category prediction can itself be wrong. A hard-coded category penalty could therefore remove or reduce the score of a visually correct item.

For this reason, category reranking was measured separately but was **not added as a fixed production rule**.

## 9. Why Are Open-Set Thresholds Explicitly Provisional?

A useful matcher should be able to indicate that no catalogue item is a sufficiently good match.

We implemented three provisional states:

* `MATCH`: similarity ≥ 0.85
* `UNCERTAIN`: similarity between 0.78 and 0.85
* `NO_MATCH`: similarity < 0.78

These thresholds are **not calibrated confidence levels**.

A proper threshold would require a validation dataset containing both:

1. queries that genuinely belong to the catalogue, and
2. queries that are known not to belong to the catalogue.

We did not have enough verified open-set data to calibrate these thresholds scientifically. Therefore, the thresholds are explicitly marked as provisional and should be recalibrated using a larger labelled validation set.

## 10. Why Was a Synthetic Automated Stumper Used?

The assignment asks for 100 real phone photographs with known catalogue ground truth.

We were not able to complete that physical-photo collection within the available development time.

Instead of presenting unverified physical photos as measured accuracy, we created an **automated synthetic stress test**.

The experiment used:

* 50 catalogue listings
* 10 transformation conditions
* 500 generated query images
* Known ground truth by construction

The transformations included:

* bad lighting
* brightness/contrast changes
* blur
* rotation
* partial crop
* partial occlusion
* background clutter
* image noise
* perspective distortion
* combined difficult transformations

The resulting synthetic evaluation achieved:

* **Top-1: 90.40%**
* **Top-5: 95.00%**

These numbers describe the synthetic test set only. They should **not** be interpreted as accuracy on real phone photographs.

## 11. Limitations and Trade-offs

### Latency Bottleneck

The system was tested on CPU.

The final matcher validation measured approximately:

* Average CLIP encoding: **278 ms**
* Average FAISS search: **7 ms**
* Average total query latency: **286 ms**

This shows that CLIP image encoding is the main latency bottleneck rather than FAISS retrieval.

Hardware acceleration or a faster inference setup could reduce the encoding time if the system needs to handle higher traffic.

### Sim-to-Real Gap

The automated stumper provides controlled tests with known ground truth, but synthetic transformations cannot fully reproduce the behaviour of a real phone camera.

Real photographs can contain effects such as complex lighting, reflections, camera exposure changes, hand occlusion, motion blur and backgrounds that are difficult to model exactly.

We therefore also tested four physical accessory photographs separately. Those photos did not have verified catalogue matches, so they were treated as **exploratory real-world tests rather than accuracy measurements**.

### Missing Real-Photo Ground Truth

The seven official query images and four physical reference photos were used for functionality, retrieval behaviour and qualitative analysis.

Because their correct catalogue listing IDs were not independently verified, we did not report an accuracy percentage for them.

### Catalogue Reproducibility

The final metadata and FAISS index are included with the project so that the matcher can be run without rebuilding the catalogue.

The downloaded catalogue images are kept outside Git because of their size. Rebuilding the index from the original catalogue therefore requires repeating the documented catalogue acquisition and image-download process.

### Overall Trade-off

The final system intentionally uses a simple exact-retrieval architecture:

**Image → CLIP embedding → normalized vector → FAISS exact search → Top-20 → Top-5 unique listings → provisional open-set decision**

More complex approaches such as category reranking and multi-crop retrieval were investigated, but were not promoted to the production pipeline without sufficient verified evaluation data.
