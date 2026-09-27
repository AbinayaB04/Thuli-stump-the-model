# Physical Item Matching Instructions

Because you are using physical accessories you already own, we need to map them to the catalogue to guarantee they exist in the 5,144-product database before including them in the Stumper dataset. 

## How to use the helper workflow:

1. **Take Reference Photos**: Take exactly ONE clear reference photo of each physical jewelry piece you own. 
2. **Add to Directory**: Place these reference photos (e.g. `my_ring.jpg`, `blue_necklace.png`) into the following directory:
   `data/stumper/physical_reference/`
3. **Run the Script**: Execute the helper script:
   ```bash
   python src/find_physical_item_matches.py
   ```
4. **Review Candidates**: The script will encode your photos, search the production FAISS index, and output the Top-10 candidates for each reference item. Look at the generated contact sheets located in:
   `results/stumper/physical_candidates/`
   
## Important Rules for the Stumper Dataset:

* **DO NOT** assume the Top-1 candidate is automatically the correct item. You must use your human judgment to visually confirm if the physical item exactly matches a catalogue listing.
* **ONLY USE** physical accessories that have a genuine, confirmed matching catalogue listing. If a physical piece you own does not exist in the catalogue, do not use it for the final Stump the Model dataset.
* Once you have identified a confirmed `listing_id` for your physical item from the contact sheet, you can proceed to photograph that specific item in the 10 various required conditions, placing them in `data/stumper/images/<condition>/` and noting the ID in `metadata.csv`.
* The script does **not** create ground-truth labels and does **not** modify the catalogue, index, or matcher. It is strictly a visual aid for you.
