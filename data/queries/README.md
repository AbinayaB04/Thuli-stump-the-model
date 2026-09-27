# Official Query Mapping Guide

**IMPORTANT:** The images currently located in `data/queries/images/` are the **ONLY** official query/test images for the Stump the Model assignment. 

Any older test images that may have shared these filenames, along with their associated ground-truth mappings, predictions, and categories, are completely **invalid** and have been backed up/removed. Do NOT rely on any past evaluation files (e.g. `evaluation_old.csv`) to determine the ground truth for these images.

## Ground Truth Setup
To evaluate the baseline retrieval system with these official queries, we need a fresh "ground truth" mapping that links each photograph directly to the corresponding physical item in our Etsy catalogue.

We have generated a blank template file for you to fill out:
**`data/queries/query_mapping_template.csv`**

### How to Fill out the Mapping

1. Open `data/queries/query_mapping_template.csv` (or the equivalent `data/queries/evaluation.csv`).
2. For each `query_image` (e.g., `test1.jpeg`), identify the exact piece of jewelry depicted. **Do NOT use visual similarity predictions from the model.** 
3. Look up that physical item in `data/catalogue/etsy/catalogue_clean.csv` and find its 9-digit `listing_id`.
4. Enter the `listing_id` into the `actual_listing_id` column. 
5. Enter the correct category into `actual_category` (e.g., `ring`, `earring`, `necklace`, `bracelet`, `pendant`).
6. Enter the conditions of the photograph as a comma-separated string in the `condition` column. See the accepted conditions below.
7. Ensure your changes are saved to **`data/queries/evaluation.csv`**.

### Accepted Conditions
Please describe the conditions of the phone photo using one or more of the following:
* `good_lighting`
* `low_light`
* `odd_angle`
* `partial_occlusion`
* `cluttered_background`
* `blur`
* `reflection`
* `hand_or_wrist`
* `partial_view`

## Running Evaluation
**WAIT:** Do NOT run the evaluation script until all `actual_listing_id` fields have been verified and manually filled out. 

Once `evaluation.csv` is filled out with the verified ground truth, run:
```bash
python -m src.evaluate
```
