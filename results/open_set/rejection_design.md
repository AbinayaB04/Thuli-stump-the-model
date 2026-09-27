# Open-Set Rejection Layer Design

## Why Open-Set Rejection is Needed
In a real-world scenario (Part A of Stump the Model), the user provides an arbitrary photo from their phone. Unlike closed-set evaluation where it's guaranteed that the queried image corresponds to a known catalogue item, real-world queries may include items completely absent from the 5,144-product catalogue. 

Without a rejection layer, the model will always retrieve the nearest visual match and incorrectly present it as a correct match. An open-set rejection layer prevents these "hallucinated" matches by determining if the closest candidate is actually the exact same product or just the closest wrong answer.

## Signal Used
We rely strictly on the **Top-1 CLIP inner-product (cosine) similarity score**. We do *not* pretend this is a calibrated probability or a normalized confidence score, as deep neural embeddings do not natively map similarity directly to probabilistic confidence without calibration.

## Threshold Strategy
We must clearly distinguish between the structural rejection mechanism, the current placeholder thresholds, and future calibrated thresholds.

1. **Implemented Rejection Mechanism**: A dual-threshold structural layer capable of handling `MATCH`, `UNCERTAIN`, and `NO_MATCH` logic.
2. **Provisional Placeholder Thresholds**: The values currently assigned (`0.85` and `0.78`) are purely architectural constants (`THRESHOLD_STATUS = "UNVALIDATED_PLACEHOLDER"`). They are NOT scientifically validated and should not be trusted for production accuracy.
3. **Scientifically Validated Thresholds**: True thresholds that will be learned empirically once sufficient validation data is collected.

## How this would be calibrated with a proper validation set
To replace the provisional placeholders with scientifically validated thresholds, calibration requires:
1. **Verified Catalogue-Match Query Photos (In-Distribution)**: Real-world photos of physical items known to exist in the catalogue.
2. **Verified Non-Catalogue Query Photos (Out-of-Distribution)**: Real-world photos of physical items known *not* to exist in the catalogue.
3. **Similarity Distributions**: We must compute the Top-1 similarity scores for both groups and plot their histograms.
4. **Threshold Selection**: By analyzing the overlap between the two distributions, we select thresholds based on the desired trade-off between the False Accept Rate (FAR) and False Reject Rate (FRR).

## Limitations
- **No Calibrated Confidence**: The current similarity scores are uncalibrated. 
- **Insufficient Labelled Data**: We currently do not have enough strictly labeled in-distribution and out-of-distribution photos to scientifically set the `high_threshold` and `low_threshold`. The current values (e.g., 0.85, 0.78) are speculative placeholders and must not be treated as ground truth logic in production until calibrated.
- **Top-5 Preserved**: The matcher still prints the Top-5 candidates even when predicting `NO_MATCH` to aid in debugging, engineering, and threshold adjustment.
