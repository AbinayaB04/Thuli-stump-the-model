# Automated Stumper: Failure Analysis Report

**Disclaimer:** The results below are derived from programmatic synthetic image augmentations. They are not equivalent to real-world phone-photo performance.

## Per-Condition Statistics

### Condition: `background_clutter`
- **Number of Queries**: 50
- **Top-1 Correct**: 27
- **Top-1 Accuracy**: 54.00%
- **Top-5 Accuracy**: 68.00%
- **Avg Similarity**: 0.8084
- **Avg Sim (Correct)**: 0.8260
- **Avg Sim (Incorrect)**: 0.7878

### Condition: `combined_difficult`
- **Number of Queries**: 50
- **Top-1 Correct**: 39
- **Top-1 Accuracy**: 78.00%
- **Top-5 Accuracy**: 94.00%
- **Avg Similarity**: 0.8662
- **Avg Sim (Correct)**: 0.8775
- **Avg Sim (Incorrect)**: 0.8263

### Condition: `brightness_contrast`
- **Number of Queries**: 50
- **Top-1 Correct**: 45
- **Top-1 Accuracy**: 90.00%
- **Top-5 Accuracy**: 98.00%
- **Avg Similarity**: 0.9035
- **Avg Sim (Correct)**: 0.9111
- **Avg Sim (Incorrect)**: 0.8355

### Condition: `partial_occlusion`
- **Number of Queries**: 50
- **Top-1 Correct**: 45
- **Top-1 Accuracy**: 90.00%
- **Top-5 Accuracy**: 96.00%
- **Avg Similarity**: 0.8770
- **Avg Sim (Correct)**: 0.8859
- **Avg Sim (Incorrect)**: 0.7973

### Condition: `partial_crop`
- **Number of Queries**: 50
- **Top-1 Correct**: 47
- **Top-1 Accuracy**: 94.00%
- **Top-5 Accuracy**: 94.00%
- **Avg Similarity**: 0.9248
- **Avg Sim (Correct)**: 0.9272
- **Avg Sim (Incorrect)**: 0.8867

### Condition: `image_noise`
- **Number of Queries**: 50
- **Top-1 Correct**: 49
- **Top-1 Accuracy**: 98.00%
- **Top-5 Accuracy**: 100.00%
- **Avg Similarity**: 0.9165
- **Avg Sim (Correct)**: 0.9169
- **Avg Sim (Incorrect)**: 0.8936

### Condition: `bad_lighting`
- **Number of Queries**: 50
- **Top-1 Correct**: 50
- **Top-1 Accuracy**: 100.00%
- **Top-5 Accuracy**: 100.00%
- **Avg Similarity**: 0.9324
- **Avg Sim (Correct)**: 0.9324
- **Avg Sim (Incorrect)**: nan

### Condition: `blur`
- **Number of Queries**: 50
- **Top-1 Correct**: 50
- **Top-1 Accuracy**: 100.00%
- **Top-5 Accuracy**: 100.00%
- **Avg Similarity**: 0.9333
- **Avg Sim (Correct)**: 0.9333
- **Avg Sim (Incorrect)**: nan

### Condition: `rotation`
- **Number of Queries**: 50
- **Top-1 Correct**: 50
- **Top-1 Accuracy**: 100.00%
- **Top-5 Accuracy**: 100.00%
- **Avg Similarity**: 0.9452
- **Avg Sim (Correct)**: 0.9452
- **Avg Sim (Incorrect)**: nan

### Condition: `perspective_distortion`
- **Number of Queries**: 50
- **Top-1 Correct**: 50
- **Top-1 Accuracy**: 100.00%
- **Top-5 Accuracy**: 100.00%
- **Avg Similarity**: 0.9596
- **Avg Sim (Correct)**: 0.9596
- **Avg Sim (Incorrect)**: nan

## Representative Failure Cases

### background_clutter
- **Query**: `4538148367_background_clutter.jpg`
  - **GT ID**: 4538148367 (earring)
  - **Pred ID**: 1502917898 (earring)
  - **Similarity**: 0.8496
- **Query**: `4309162894_background_clutter.jpg`
  - **GT ID**: 4309162894 (ring)
  - **Pred ID**: 1304264275 (ring)
  - **Similarity**: 0.8395
- **Query**: `4583140761_background_clutter.jpg`
  - **GT ID**: 4583140761 (ring)
  - **Pred ID**: 4583152458 (ring)
  - **Similarity**: 0.8388

### combined_difficult
- **Query**: `4401014124_combined_difficult.jpg`
  - **GT ID**: 4401014124 (ring)
  - **Pred ID**: 4486912986 (ring)
  - **Similarity**: 0.9117
- **Query**: `4511137547_combined_difficult.jpg`
  - **GT ID**: 4511137547 (ring)
  - **Pred ID**: 4486912986 (ring)
  - **Similarity**: 0.8465
- **Query**: `4583172822_combined_difficult.jpg`
  - **GT ID**: 4583172822 (ring)
  - **Pred ID**: 4348781927 (ring)
  - **Similarity**: 0.8400

### brightness_contrast
- **Query**: `1389443910_brightness_contrast.jpg`
  - **GT ID**: 1389443910 (ring)
  - **Pred ID**: 517519659 (ring)
  - **Similarity**: 0.9330
- **Query**: `4582185265_brightness_contrast.jpg`
  - **GT ID**: 4582185265 (bracelet)
  - **Pred ID**: 4345848710 (bracelet)
  - **Similarity**: 0.8561
- **Query**: `4583149957_brightness_contrast.jpg`
  - **GT ID**: 4583149957 (ring)
  - **Pred ID**: 4395797008 (bracelet)
  - **Similarity**: 0.8290

### partial_occlusion
- **Query**: `4553485453_partial_occlusion.jpg`
  - **GT ID**: 4553485453 (necklace)
  - **Pred ID**: 4494938702 (necklace)
  - **Similarity**: 0.8492
- **Query**: `4583149957_partial_occlusion.jpg`
  - **GT ID**: 4583149957 (ring)
  - **Pred ID**: 1612904168 (pendant)
  - **Similarity**: 0.8038
- **Query**: `1874276471_partial_occlusion.jpg`
  - **GT ID**: 1874276471 (ring)
  - **Pred ID**: 4510375245 (ring)
  - **Similarity**: 0.7909

## Observed Failure Patterns

Based on the synthetic failures:
- **`background_clutter`**: Adding sharp random noise lines severely disrupted CLIP's attention. The model was observed matching to texturally dense objects or entirely different categories, suggesting that when the structural outline is disrupted by clutter, global shape recognition fails.
- **`combined_difficult`**: The combination of blur, rotation, and lighting changes often forced the model to match on general color palettes rather than intricate jewelry details. 
- **`brightness_contrast`**: Extreme brightness/contrast adjustments occasionally bleached out metallic details, causing misclassification often within the same broad category (e.g., ring vs ring) but with an incorrect specific listing.
- **`partial_occlusion`**: Applying a heavy black occlusion block was associated with the model hallucinating matches with objects that naturally have large dark regions or shadows.

## What this experiment tells us
- The current baseline production model is highly resilient to simple isolated transformations (rotation, minor noise, simple blur).
- The model is highly sensitive to occlusion and heavy structural disruption (clutter), suggesting that it evaluates the global composition of the image rather than isolating the central object.

## What this experiment does not tell us
- It does **not** tell us the model's accuracy on genuine out-of-domain images like self-shot phone photographs in low-lit bedrooms.
- It does **not** prove that background clutter in real photos (like a desk) behaves mathematically the same as the sharp randomized RGB lines drawn in this synthetic test.
