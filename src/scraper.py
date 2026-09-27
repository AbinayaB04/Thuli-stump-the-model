import os
import time
import random
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://api.etsy.com/v3/application"

OUTPUT_DIR = Path("data/catalogue/etsy")
IMAGE_DIR = OUTPUT_DIR / "images"

CATALOGUE_CSV = OUTPUT_DIR / "catalogue.csv"
FAILED_CSV = OUTPUT_DIR / "failed.csv"

# ------------------------------------------------------------
# CHANGE THIS NUMBER
# ------------------------------------------------------------
#
# For testing:
#     100
#
# Then:
#     500
#     1000
#     5000
#
TARGET_ITEMS = 5000



# ============================================================
# BALANCED CATEGORY TARGETS
# ============================================================
#
# For 100 items:
#
# ring       = 20
# earring    = 20
# bracelet   = 20
# necklace   = 20
# pendant    = 15
# anklet     = 5
#
# TOTAL = 100
#
# The script automatically scales these percentages when
# TARGET_ITEMS changes.
# ============================================================

CATEGORY_RATIOS = {
    "ring": 0.20,
    "earring": 0.20,
    "bracelet": 0.20,
    "necklace": 0.20,
    "pendant": 0.15,
    "anklet": 0.05,
}


# ============================================================
# SEARCH TERMS
# ============================================================
#
# Multiple search terms help avoid getting almost identical
# results from one Etsy search.
# ============================================================

SEARCH_TERMS = {
    "ring": [
        "ring",
        "gold ring",
        "silver ring",
        "gemstone ring",
        "statement ring",
        "diamond ring",
    ],

    "earring": [
        "earrings",
        "gold earrings",
        "silver earrings",
        "stud earrings",
        "drop earrings",
        "dangle earrings",
        "hoop earrings",
        "jhumka earrings",
    ],

    "bracelet": [
        "bracelet",
        "gold bracelet",
        "silver bracelet",
        "chain bracelet",
        "cuff bracelet",
        "bangle",
        "bangles",
    ],

    "necklace": [
        "necklace",
        "gold necklace",
        "silver necklace",
        "chain necklace",
        "statement necklace",
        "layered necklace",
    ],

    "pendant": [
        "pendant",
        "gold pendant",
        "silver pendant",
        "pendant necklace",
        "gemstone pendant",
    ],

    "anklet": [
        "anklet",
        "anklets",
        "ankle bracelet",
        "silver anklet",
        "gold anklet",
    ],
}


# ============================================================
# OBVIOUSLY IRRELEVANT TITLE WORDS
# ============================================================

EXCLUDED_TITLE_WORDS = [
    "supply",
    "supplies",
    "beads",
    "bead",
    "jewelry making",
    "jewellery making",
    "jewelry tool",
    "jewellery tool",
    "craft tool",
    "craft supplies",
    "making kit",
    "diy kit",
    "template",
    "pattern",
    "digital download",
    "digital file",
    "printable",
    "svg",
    "laser cut",
    "sticker",
    "packaging",
    "jewelry box",
    "jewellery box",
    "display stand",
    "display card",
    "business card",
    "instruction",
    "tutorial",
]


# ============================================================
# CATEGORY-SPECIFIC EXCLUSIONS
# ============================================================

CATEGORY_EXCLUSIONS = {

    "ring": [
        "ring dish",
        "ring holder",
        "ring box",
        "ring sizer",
        "ring mandrel",
        "ring light",
        "ring stand",
    ],

    "earring": [
        "earring card",
        "earring holder",
        "earring display",
        "earring backs",
        "earring finding",
        "earring hooks",
    ],

    "bracelet": [
        "bracelet making",
        "bracelet kit",
        "bracelet pattern",
        "bracelet display",
        "bracelet holder",
    ],

    "necklace": [
        "necklace display",
        "necklace holder",
        "necklace stand",
        "necklace making",
        "necklace chain only",
    ],

    "pendant": [
        "pendant setting",
        "pendant blank",
        "pendant mold",
        "pendant display",
        "pendant holder",
    ],

    "anklet": [
        "anklet making",
        "anklet display",
        "anklet holder",
    ],
}


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("ETSY_API_KEY")
SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET")

if not API_KEY or not SHARED_SECRET:

    print("=" * 70)
    print("ERROR")
    print("=" * 70)

    print(
        "ETSY_API_KEY or ETSY_SHARED_SECRET is missing."
    )

    print()
    print("Check your .env file.")

    raise SystemExit(1)


# ============================================================
# ETSY SESSION
# ============================================================

session = requests.Session()

retry_strategy = Retry(
    total=5,
    connect=5,
    read=5,
    status=5,
    backoff_factor=2,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504,
    ],
    allowed_methods=[
        "GET",
    ],
    raise_on_status=False,
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,
    pool_maxsize=10,
)

session.mount(
    "https://",
    adapter
)

session.mount(
    "http://",
    adapter
)

session.headers.update({
    "x-api-key": f"{API_KEY}:{SHARED_SECRET}",
    "User-Agent": "Thuli-Stump-The-Model/1.0",
})


# ============================================================
# CREATE DIRECTORIES
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

IMAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_category_targets(target_items):
    """
    Convert category ratios into integer targets.
    """

    targets = {}

    remaining = target_items

    categories = list(
        CATEGORY_RATIOS.keys()
    )

    for i, category in enumerate(categories):

        if i == len(categories) - 1:

            targets[category] = remaining

        else:

            count = round(
                target_items
                * CATEGORY_RATIOS[category]
            )

            targets[category] = count

            remaining -= count

    return targets


def load_existing_catalogue():
    """
    Load existing catalogue so the script can resume.
    """

    if not CATALOGUE_CSV.exists():

        return pd.DataFrame()

    try:

        df = pd.read_csv(
            CATALOGUE_CSV
        )

        print(
            f"Loaded existing catalogue: {len(df)} items"
        )

        return df

    except Exception as e:

        print(
            f"Warning: could not read existing catalogue: {e}"
        )

        return pd.DataFrame()


def load_failed():
    """
    Load previously failed downloads.
    """

    if not FAILED_CSV.exists():

        return pd.DataFrame()

    try:

        return pd.read_csv(
            FAILED_CSV
        )

    except Exception:

        return pd.DataFrame()


def save_catalogue(df):
    """
    Save catalogue immediately.
    """

    df.to_csv(
        CATALOGUE_CSV,
        index=False,
        encoding="utf-8"
    )


def save_failed(df):
    """
    Save failed downloads immediately.
    """

    df.to_csv(
        FAILED_CSV,
        index=False,
        encoding="utf-8"
    )


def title_is_relevant(
    title,
    category
):
    """
    Reject obvious supplies/tools/non-product listings.
    """

    if not isinstance(title, str):

        return False

    title_lower = title.lower()

    # General exclusions
    for word in EXCLUDED_TITLE_WORDS:

        if word in title_lower:

            return False

    # Category-specific exclusions
    exclusions = CATEGORY_EXCLUSIONS.get(
        category,
        []
    )

    for word in exclusions:

        if word in title_lower:

            return False

    return True


def listing_matches_category(
    title,
    category
):
    """
    Basic title-level category validation.

    This is intentionally conservative.
    """

    if not isinstance(title, str):

        return False

    title_lower = title.lower()

    if category == "ring":

        return (
            "ring" in title_lower
            and "earring" not in title_lower
        )

    if category == "earring":

        return (
            "earring" in title_lower
            or "earrings" in title_lower
            or "jhumka" in title_lower
            or "stud earring" in title_lower
            or "dangle earring" in title_lower
            or "drop earring" in title_lower
            or "hoop earring" in title_lower
        )

    if category == "bracelet":

        return (
            "bracelet" in title_lower
            or "bangle" in title_lower
            or "bangles" in title_lower
        )

    if category == "necklace":

        return (
            "necklace" in title_lower
        )

    if category == "pendant":

        return (
            "pendant" in title_lower
        )

    if category == "anklet":

        return (
            "anklet" in title_lower
            or "anklets" in title_lower
            or "ankle bracelet" in title_lower
        )

    return False


def get_listing_images(
    listing_id
):
    """
    Retrieve images from Etsy's listing-images endpoint.
    """

    url = (
        f"{BASE_URL}/listings/"
        f"{listing_id}/images"
    )

    try:

        response = session.get(
            url,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"Image API status: "
                f"{response.status_code}"
            )

            return []

        data = response.json()

        return data.get(
            "results",
            []
        )

    except Exception as e:

        print(
            f"Image API error: {e}"
        )

        return []


def download_image(
    image_url,
    destination
):
    """
    Download and validate an image.
    """

    for attempt in range(1, 6):

        try:

            response = session.get(
                image_url,
                timeout=45
            )

            if response.status_code != 200:

                print(
                    f"Download status "
                    f"{response.status_code}"
                )

                time.sleep(
                    2 ** attempt
                )

                continue

            image_data = response.content

            image = Image.open(
                BytesIO(image_data)
            )

            # Force actual decoding
            image.load()

            # Convert to RGB
            image = image.convert(
                "RGB"
            )

            # Basic size check
            width, height = image.size

            if width < 200 or height < 200:

                print(
                    f"Image too small: "
                    f"{width}x{height}"
                )

                return False

            image.save(
                destination,
                "JPEG",
                quality=95
            )

            return True

        except Exception as e:

            print(
                f"Download attempt "
                f"{attempt}/5 failed: {e}"
            )

            time.sleep(
                2 ** attempt
            )

    return False


def search_listings(
    keyword,
    offset
):
    """
    Search active Etsy listings.
    """

    url = (
        f"{BASE_URL}/listings/active"
    )

    params = {
        "limit": 100,
        "offset": offset,
        "keywords": keyword,
    }

    try:

        response = session.get(
            url,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"Search status "
                f"{response.status_code}"
            )

            print(
                response.text[:300]
            )

            return None

        return response.json()

    except Exception as e:

        print(
            f"Search error: {e}"
        )

        return None


def choose_image_url(images):
    """
    Prefer medium-sized image to avoid unnecessarily
    huge downloads.
    """

    if not images:

        return None

    image = images[0]

    # Prefer 570px image
    if image.get("url_570xN"):

        return image[
            "url_570xN"
        ]

    # Fallback
    if image.get("url_fullxfull"):

        return image[
            "url_fullxfull"
        ]

    # Other possible Etsy image fields
    for key in [
        "url_224xN",
        "url_300x300",
        "url_170x135",
    ]:

        if image.get(key):

            return image[key]

    return None


def get_category_counts(df):
    """
    Return counts by category.
    """

    counts = {}

    for category in CATEGORY_RATIOS:

        if df.empty:

            counts[category] = 0

        else:

            counts[category] = int(
                (
                    df["category"]
                    == category
                ).sum()
            )

    return counts


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect(
    target_items=100
):

    print()
    print("=" * 70)
    print("THULI JEWELLERY CATALOGUE COLLECTOR")
    print("=" * 70)

    targets = get_category_targets(
        target_items
    )

    print()
    print("Target distribution:")
    print()

    for category, target in targets.items():

        print(
            f"{category:<12} {target}"
        )

    print()
    print(
        f"Total target: {sum(targets.values())}"
    )

    # --------------------------------------------------------
    # Load existing data
    # --------------------------------------------------------

    catalogue_df = load_existing_catalogue()
    failed_df = load_failed()

    if catalogue_df.empty:

        catalogue_df = pd.DataFrame(
            columns=[
                "item_id",
                "title",
                "category",
                "image_url",
                "local_image_path",
                "etsy_url",
                "search_keyword",
            ]
        )

    # --------------------------------------------------------
    # Existing listing IDs
    # --------------------------------------------------------

    existing_ids = set()

    if not catalogue_df.empty:

        existing_ids = set(
            catalogue_df[
                "item_id"
            ].astype(str)
        )

    # --------------------------------------------------------
    # Current category counts
    # --------------------------------------------------------

    counts = get_category_counts(
        catalogue_df
    )

    print()
    print("Existing category counts:")

    for category in targets:

        print(
            f"{category:<12} "
            f"{counts.get(category, 0)} / "
            f"{targets[category]}"
        )

    # --------------------------------------------------------
    # Main category loop
    # --------------------------------------------------------

    for category, target in targets.items():

        current_count = counts.get(
            category,
            0
        )

        if current_count >= target:

            print()
            print(
                f"{category}: target already reached."
            )

            continue

        print()
        print("=" * 70)
        print(
            f"COLLECTING CATEGORY: "
            f"{category.upper()}"
        )
        print(
            f"Current: {current_count}"
        )
        print(
            f"Target:  {target}"
        )
        print("=" * 70)

        category_search_terms = (
            SEARCH_TERMS[category]
        )

        search_index = 0

        # ----------------------------------------------------
        # Continue searching until quota is reached
        # ----------------------------------------------------

        while current_count < target:

            keyword = category_search_terms[
                search_index
                % len(category_search_terms)
            ]

            print()
            print(
                f"Search keyword: {keyword}"
            )

            offset = 0

            pages_without_progress = 0

            # ------------------------------------------------
            # Pagination
            # ------------------------------------------------

            while (
                current_count < target
                and offset <= 12000
            ):

                print()
                print(
                    f"Category: {category}"
                )

                print(
                    f"Keyword: {keyword}"
                )

                print(
                    f"Offset: {offset}"
                )

                data = search_listings(
                    keyword,
                    offset
                )

                if not data:

                    print(
                        "Search failed. "
                        "Trying next keyword..."
                    )

                    break

                listings = data.get(
                    "results",
                    []
                )

                if not listings:

                    print(
                        "No more results "
                        "for this keyword."
                    )

                    break

                print(
                    f"Found {len(listings)} listings"
                )

                page_added = 0

                # --------------------------------------------
                # Process listings
                # --------------------------------------------

                for listing in listings:

                    if current_count >= target:

                        break

                    listing_id = str(
                        listing.get(
                            "listing_id",
                            ""
                        )
                    )

                    if not listing_id:

                        continue

                    # ----------------------------------------
                    # Skip existing listing
                    # ----------------------------------------

                    if listing_id in existing_ids:

                        continue

                    title = listing.get(
                        "title",
                        ""
                    )

                    # ----------------------------------------
                    # Title filter
                    # ----------------------------------------

                    if not title_is_relevant(
                        title,
                        category
                    ):

                        continue

                    # ----------------------------------------
                    # Category filter
                    # ----------------------------------------

                    if not listing_matches_category(
                        title,
                        category
                    ):

                        continue

                    print()
                    print(
                        "-" * 60
                    )

                    print(
                        f"Listing "
                        f"{current_count + 1}/"
                        f"{target}"
                    )

                    print(
                        f"ID: {listing_id}"
                    )

                    print(
                        f"Category: {category}"
                    )

                    print(
                        f"Title: {title}"
                    )

                    # ----------------------------------------
                    # Get listing images
                    # ----------------------------------------

                    images = get_listing_images(
                        listing_id
                    )

                    if not images:

                        print(
                            "No images found."
                        )

                        continue

                    image_url = choose_image_url(
                        images
                    )

                    if not image_url:

                        print(
                            "Could not find "
                            "usable image URL."
                        )

                        continue

                    # ----------------------------------------
                    # Download image
                    # ----------------------------------------

                    image_filename = (
                        f"{listing_id}.jpg"
                    )

                    image_path = (
                        IMAGE_DIR
                        / image_filename
                    )

                    # If file somehow already exists,
                    # don't download again.
                    if image_path.exists():

                        print(
                            "Image already exists. "
                            "Using existing file."
                        )

                    else:

                        print(
                            "Downloading image..."
                        )

                        success = download_image(
                            image_url,
                            image_path
                        )

                        if not success:

                            print(
                                "Image download failed."
                            )

                            failed_row = {
                                "item_id": listing_id,
                                "title": title,
                                "category": category,
                                "image_url": image_url,
                                "reason": "download_failed",
                            }

                            failed_df = pd.concat(
                                [
                                    failed_df,
                                    pd.DataFrame(
                                        [failed_row]
                                    ),
                                ],
                                ignore_index=True
                            )

                            save_failed(
                                failed_df
                            )

                            continue

                    # ----------------------------------------
                    # Etsy URL
                    # ----------------------------------------

                    etsy_url = (
                        "https://www.etsy.com/"
                        f"listing/{listing_id}"
                    )

                    # ----------------------------------------
                    # Add catalogue row
                    # ----------------------------------------

                    new_row = {
                        "item_id": listing_id,
                        "title": title,
                        "category": category,
                        "image_url": image_url,
                        "local_image_path": str(
                            image_path
                        ),
                        "etsy_url": etsy_url,
                        "search_keyword": keyword,
                    }

                    catalogue_df = pd.concat(
                        [
                            catalogue_df,
                            pd.DataFrame(
                                [new_row]
                            ),
                        ],
                        ignore_index=True
                    )

                    # ----------------------------------------
                    # Update tracking
                    # ----------------------------------------

                    existing_ids.add(
                        listing_id
                    )

                    current_count += 1
                    page_added += 1

                    counts[category] = (
                        current_count
                    )

                    # ----------------------------------------
                    # SAVE IMMEDIATELY
                    # ----------------------------------------

                    save_catalogue(
                        catalogue_df
                    )

                    print(
                        f"Saved successfully."
                    )

                    print(
                        f"Progress: "
                        f"{current_count}/{target}"
                    )

                    # Avoid hammering Etsy
                    time.sleep(
                        random.uniform(
                            0.8,
                            1.5
                        )
                    )

                # --------------------------------------------
                # Page progress
                # --------------------------------------------

                if page_added == 0:

                    pages_without_progress += 1

                else:

                    pages_without_progress = 0

                if current_count >= target:

                    break

                # If several pages produce nothing,
                # move to another keyword.
                if pages_without_progress >= 3:

                    print(
                        "No useful listings found "
                        "for several pages."
                    )

                    break

                offset += 100

                # Etsy offset safety
                if offset > 12000:

                    break

                time.sleep(
                    random.uniform(
                        1.5,
                        3.0
                    )
                )

            # --------------------------------------------
            # Next search keyword
            # --------------------------------------------

            search_index += 1

            if search_index >= len(
                category_search_terms
            ):

                # We have exhausted the keyword list.
                # Start over with keywords but deeper
                # pagination.
                search_index = 0

                print()
                print(
                    f"All search keywords exhausted "
                    f"for {category}."
                )

                print(
                    "Continuing with broader search."
                )

                # If still no progress after all terms,
                # prevent infinite looping.
                if current_count < target:

                    print(
                        f"Warning: unable to reach "
                        f"target for {category} "
                        f"with current filters."
                    )

                    break

        print()
        print(
            f"Finished {category}: "
            f"{current_count}/{target}"
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)

    final_counts = get_category_counts(
        catalogue_df
    )

    print()

    for category in targets:

        print(
            f"{category:<12} "
            f"{final_counts.get(category, 0)} / "
            f"{targets[category]}"
        )

    print()
    print(
        f"Total collected: {len(catalogue_df)}"
    )

    print()
    print(
        f"Catalogue CSV:"
    )

    print(
        f"  {CATALOGUE_CSV}"
    )

    print()
    print(
        f"Images:"
    )

    print(
        f"  {IMAGE_DIR}"
    )

    print()
    print(
        f"Failed downloads:"
    )

    print(
        f"  {FAILED_CSV}"
    )

    print()
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    collect(
        target_items=TARGET_ITEMS
    )