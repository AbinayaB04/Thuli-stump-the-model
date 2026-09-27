# Stump the Model Evaluation Dataset

## Overview
This directory is prepared for the required 100+ phone-photo "Stump the Model" evaluation. 

## Collection Plan
A reproducible, random sample of 20 unique catalogue products has been selected (see `catalogue_sampling.csv`). 

To complete this assignment:
1. Locate or obtain the actual physical item represented by each of the 20 selected catalogue listings.
2. Photograph each item under 5 or more different conditions. 
   - 20 catalogue products × 5 conditions = at least 100 photos.
3. Place the resulting phone photos in the corresponding condition subdirectories inside `images/`.

### Recommended Conditions:
- `normal`
- `bad_lighting`
- `odd_angle`
- `partial_occlusion`
- `clutter`
- `motion_blur`
- `reflection`
- `hand_wrist`
- `far_distance`
- `cropped`

## Metadata
Once photos are collected, update `metadata.csv` with the corresponding `query_image`, `catalogue_listing_id`, `category`, and any `conditions` or `notes`. 

> **Important**: Do NOT assume the original catalogue images themselves are phone photos. The catalogue image serves only as the baseline target to retrieve. Do NOT automatically populate `catalogue_listing_id` until the real physical photos are actually collected.
