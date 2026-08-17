import serpapi
import os
import csv
import time

from dotenv import load_dotenv
from datetime import datetime, date


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

api_key = os.getenv("SERPAPI_KEY")

if not api_key:
    raise ValueError(
        "SERPAPI_KEY not found.\n"
        "Make sure your .env file contains:\n\n"
        "SERPAPI_KEY=your_api_key"
    )

client = serpapi.Client(api_key=api_key)


# ============================================================
# DATE RANGE
# ============================================================

START_DATE = date(2026, 5, 1)
END_DATE = date(2026, 8, 13)

OUTPUT_FILE = "gails_reviews_may_to_august_2026.csv"

REQUEST_DELAY = 2


# ============================================================
# DATE PARSER
# ============================================================

def parse_iso_date(value):

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()

    except (ValueError, TypeError):
        return None


# ============================================================
# REVIEW TEXT
# ============================================================

def get_review_text(review):

    extracted = (
        review.get("extracted_snippet")
        or {}
    )

    # Original text
    original = extracted.get("original")

    if original:
        return original.strip()

    # Translated text
    translated = extracted.get("translated")

    if translated:
        return translated.strip()

    # Normal snippet
    snippet = review.get("snippet")

    if snippet:
        return snippet.strip()

    return ""


# ============================================================
# GET DETAIL VALUE
# ============================================================

def get_detail(details, *keys):

    """
    Finds a detail regardless of capitalization.

    Example:
        get_detail(details, "food")
        get_detail(details, "service")
    """

    if not details:
        return ""

    # Exact matches first
    for key in keys:

        if key in details:
            return details[key]

    # Case-insensitive matches
    normalized = {
        str(k).lower().strip(): v
        for k, v in details.items()
    }

    for key in keys:

        value = normalized.get(
            key.lower().strip()
        )

        if value is not None:
            return value

    return ""


# ============================================================
# OWNER RESPONSE
# ============================================================

def get_owner_response(review):

    response = (
        review.get("response")
        or {}
    )

    if not response:
        return {
            "response_date": "",
            "response_text": "",
        }

    extracted = (
        response.get(
            "extracted_snippet"
        )
        or {}
    )

    response_text = ""

    if extracted.get("original"):

        response_text = (
            extracted["original"]
        )

    elif extracted.get("translated"):

        response_text = (
            extracted["translated"]
        )

    elif response.get("snippet"):

        response_text = (
            response["snippet"]
        )

    return {
        "response_date": (
            response.get(
                "iso_date",
                ""
            )
        ),

        "response_text": (
            response_text.strip()
        ),
    }


# ============================================================
# DETERMINE REVIEW TYPE
# ============================================================

def determine_review_type(
    review_text,
    details
):

    has_text = bool(
        review_text.strip()
    )

    has_details = bool(details)

    if has_text and has_details:
        return "written_and_structured"

    if has_text:
        return "written"

    if has_details:
        return "structured"

    return "rating_only"


# ============================================================
# FETCH REVIEWS
# ============================================================

def fetch_reviews(data_id):

    all_reviews = []

    seen_review_ids = set()

    next_page_token = None

    page_number = 1

    while True:

        print("\n" + "=" * 70)
        print(f"PAGE {page_number}")
        print("=" * 70)

        # ====================================================
        # API PARAMETERS
        # ====================================================

        search_params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "sort_by": "newestFirst",
            "hl": "en",
        }

        if next_page_token:

            search_params[
                "next_page_token"
            ] = next_page_token

        print("Requesting SerpApi...")

        # ====================================================
        # REQUEST
        # ====================================================

        try:

            results = client.search(
                search_params
            )

        except Exception as e:

            print(
                "\nSERPAPI REQUEST FAILED:"
            )

            print(e)

            break

        # ====================================================
        # ERROR
        # ====================================================

        if "error" in results:

            print(
                "\nSERPAPI ERROR:"
            )

            print(
                results["error"]
            )

            break

        # ====================================================
        # REVIEWS
        # ====================================================

        reviews = (
            results.get("reviews")
            or []
        )

        print(
            f"Reviews returned: "
            f"{len(reviews)}"
        )

        if not reviews:

            print(
                "No reviews returned."
            )

            print(
                "Response keys:"
            )

            print(
                list(results.keys())
            )

            break

        # ====================================================
        # PAGE DATE TRACKING
        # ====================================================

        old_reviews_on_page = 0

        # ====================================================
        # PROCESS REVIEWS
        # ====================================================

        for index, review in enumerate(
            reviews,
            start=1
        ):

            print(
                f"\n--- Review "
                f"{index}/{len(reviews)} ---"
            )

            # =================================================
            # REVIEW ID
            # =================================================

            review_id = review.get(
                "review_id",
                ""
            )

            # =================================================
            # DATE
            # =================================================

            iso_date = review.get(
                "iso_date",
                ""
            )

            review_date = parse_iso_date(
                iso_date
            )

            raw_date = review.get(
                "date",
                ""
            )

            # -------------------------------------------------
            # No valid date
            # -------------------------------------------------

            if not review_date:

                print(
                    "WARNING: Invalid/missing date"
                )

                continue

            # =================================================
            # LAST EDITED DATE
            # =================================================

            last_edit_iso = review.get(
                "iso_date_of_last_edit",
                ""
            )

            last_edit_date = parse_iso_date(
                last_edit_iso
            )

            # =================================================
            # DATE FILTER
            # =================================================

            if review_date < START_DATE:

                print(
                    f"Old review: "
                    f"{review_date}"
                )

                old_reviews_on_page += 1

                continue

            if review_date > END_DATE:

                print(
                    f"After end date: "
                    f"{review_date}"
                )

                continue

            # =================================================
            # DUPLICATE
            # =================================================

            if review_id:

                if review_id in seen_review_ids:

                    print(
                        "Duplicate review."
                    )

                    continue

                seen_review_ids.add(
                    review_id
                )

            # =================================================
            # USER
            # =================================================

            user = (
                review.get("user")
                or {}
            )

            user_name = user.get(
                "name",
                ""
            )

            user_link = user.get(
                "link",
                ""
            )

            contributor_id = user.get(
                "contributor_id",
                ""
            )

            thumbnail = user.get(
                "thumbnail",
                ""
            )

            local_guide = user.get(
                "local_guide",
                ""
            )

            user_review_count = user.get(
                "reviews",
                ""
            )

            user_photo_count = user.get(
                "photos",
                ""
            )

            # =================================================
            # REVIEW
            # =================================================

            rating = review.get(
                "rating",
                ""
            )

            review_text = get_review_text(
                review
            )

            review_link = review.get(
                "link",
                ""
            )

            likes = review.get(
                "likes",
                0
            )

            source = review.get(
                "source",
                ""
            )

            # =================================================
            # DETAILS
            # =================================================

            details = (
                review.get("details")
                or {}
            )

            # -------------------------------------------------
            # Common Google Maps details
            # -------------------------------------------------

            food_rating = get_detail(
                details,
                "food"
            )

            service_rating = get_detail(
                details,
                "service"
            )

            atmosphere_rating = get_detail(
                details,
                "atmosphere"
            )

            # -------------------------------------------------
            # Other possible details
            # -------------------------------------------------

            order_type = get_detail(
                details,
                "order_type",
                "order type"
            )

            meal_type = get_detail(
                details,
                "meal_type",
                "meal type"
            )

            price_per_person = get_detail(
                details,
                "price_per_person",
                "price per person"
            )

            noise_level = get_detail(
                details,
                "noise_level",
                "noise level"
            )

            wait_time = get_detail(
                details,
                "wait_time",
                "wait time"
            )

            # =================================================
            # IMAGES
            # =================================================

            images = (
                review.get("images")
                or []
            )

            image_count = len(images)

            image_urls = " | ".join(
                str(image)
                for image in images
            )

            # =================================================
            # OWNER RESPONSE
            # =================================================

            owner_response = (
                get_owner_response(
                    review
                )
            )

            # =================================================
            # REVIEW TYPE
            # =================================================

            review_type = (
                determine_review_type(
                    review_text,
                    details
                )
            )

            # =================================================
            # PRINT
            # =================================================

            print(
                f"Date:       {review_date}"
            )

            print(
                f"User:       {user_name}"
            )

            print(
                f"Rating:     {rating}"
            )

            print(
                f"Type:       {review_type}"
            )

            if review_text:

                preview = review_text[:200]

                if len(review_text) > 200:
                    preview += "..."

                print(
                    f"Review:     {preview}"
                )

            else:

                print(
                    "Review:     [NO WRITTEN TEXT]"
                )

            if food_rating != "":

                print(
                    f"Food:       {food_rating}"
                )

            if service_rating != "":

                print(
                    f"Service:    {service_rating}"
                )

            if atmosphere_rating != "":

                print(
                    f"Atmosphere: {atmosphere_rating}"
                )

            if order_type:

                print(
                    f"Order type: {order_type}"
                )

            if meal_type:

                print(
                    f"Meal type:  {meal_type}"
                )

            # =================================================
            # SAVE
            # =================================================

            all_reviews.append({

                # ---------------------------------------------
                # DATE
                # ---------------------------------------------

                "date": review_date.strftime(
                    "%d/%m/%Y"
                ),

                "date_iso": (
                    iso_date
                ),

                "date_raw": raw_date,

                "last_edited_date": (
                    last_edit_date.strftime(
                        "%d/%m/%Y"
                    )
                    if last_edit_date
                    else ""
                ),

                "last_edited_date_iso": (
                    last_edit_iso
                ),

                # ---------------------------------------------
                # USER
                # ---------------------------------------------

                "user": user_name,

                "user_link": user_link,

                "contributor_id": (
                    contributor_id
                ),

                "user_thumbnail": (
                    thumbnail
                ),

                "local_guide": (
                    local_guide
                ),

                "user_review_count": (
                    user_review_count
                ),

                "user_photo_count": (
                    user_photo_count
                ),

                # ---------------------------------------------
                # REVIEW
                # ---------------------------------------------

                "rating": rating,

                "review_type": (
                    review_type
                ),

                "review": review_text,

                "review_id": review_id,

                "review_link": review_link,

                "source": source,

                "likes": likes,

                # ---------------------------------------------
                # STRUCTURED RATINGS
                # ---------------------------------------------

                "food_rating": food_rating,

                "service_rating": (
                    service_rating
                ),

                "atmosphere_rating": (
                    atmosphere_rating
                ),

                # ---------------------------------------------
                # EXPERIENCE DETAILS
                # ---------------------------------------------

                "order_type": order_type,

                "meal_type": meal_type,

                "price_per_person": (
                    price_per_person
                ),

                "noise_level": noise_level,

                "wait_time": wait_time,

                # ---------------------------------------------
                # IMAGES
                # ---------------------------------------------

                "has_images": (
                    "TRUE"
                    if image_count > 0
                    else "FALSE"
                ),

                "image_count": image_count,

                "image_urls": image_urls,

                # ---------------------------------------------
                # OWNER RESPONSE
                # ---------------------------------------------

                "owner_response_date": (
                    owner_response[
                        "response_date"
                    ]
                ),

                "owner_response": (
                    owner_response[
                        "response_text"
                    ]
                ),
            })

        # ====================================================
        # PAGINATION
        # ====================================================

        if (
            old_reviews_on_page
            == len(reviews)
        ):

            print(
                "\nEvery review on this page "
                f"is older than {START_DATE}."
            )

            print(
                "Stopping pagination."
            )

            break

        # ====================================================
        # NEXT PAGE
        # ====================================================

        pagination = (
            results.get(
                "serpapi_pagination"
            )
            or {}
        )

        next_page_token = (
            pagination.get(
                "next_page_token"
            )
        )

        if not next_page_token:

            print(
                "\nNo next page token."
            )

            print(
                "Reached final available page."
            )

            break

        print(
            "\nNext page available."
        )

        page_number += 1

        print(
            f"Waiting {REQUEST_DELAY} seconds..."
        )

        time.sleep(
            REQUEST_DELAY
        )

    return all_reviews


# ============================================================
# WRITE CSV
# ============================================================

def write_reviews_to_csv(
    reviews,
    filename
):

    # ========================================================
    # SORT NEWEST FIRST
    # ========================================================

    reviews.sort(
        key=lambda x: x["date_iso"],
        reverse=True
    )

    # ========================================================
    # COLUMNS
    # ========================================================

    fieldnames = [

        # ---------------------------------------------
        # DATE
        # ---------------------------------------------

        "date",
        "date_iso",
        "date_raw",

        "last_edited_date",
        "last_edited_date_iso",

        # ---------------------------------------------
        # USER
        # ---------------------------------------------

        "user",
        "user_link",
        "contributor_id",
        "user_thumbnail",
        "local_guide",
        "user_review_count",
        "user_photo_count",

        # ---------------------------------------------
        # REVIEW
        # ---------------------------------------------

        "rating",
        "review_type",
        "review",
        "review_id",
        "review_link",
        "source",
        "likes",

        # ---------------------------------------------
        # STRUCTURED RATINGS
        # ---------------------------------------------

        "food_rating",
        "service_rating",
        "atmosphere_rating",

        # ---------------------------------------------
        # EXPERIENCE
        # ---------------------------------------------

        "order_type",
        "meal_type",
        "price_per_person",
        "noise_level",
        "wait_time",

        # ---------------------------------------------
        # IMAGES
        # ---------------------------------------------

        "has_images",
        "image_count",
        "image_urls",

        # ---------------------------------------------
        # OWNER RESPONSE
        # ---------------------------------------------

        "owner_response_date",
        "owner_response",
    ]

    # ========================================================
    # WRITE CSV
    # ========================================================

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )

        writer.writeheader()

        writer.writerows(
            reviews
        )


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(reviews):

    print("\n")
    print("=" * 70)
    print("DATASET STATISTICS")
    print("=" * 70)

    total = len(reviews)

    print(
        f"Total reviews: {total}"
    )

    # ========================================================
    # WRITTEN VS STRUCTURED
    # ========================================================

    written = sum(
        1
        for r in reviews
        if r["review_type"]
        in (
            "written",
            "written_and_structured"
        )
    )

    structured = sum(
        1
        for r in reviews
        if r["review_type"]
        == "structured"
    )

    rating_only = sum(
        1
        for r in reviews
        if r["review_type"]
        == "rating_only"
    )

    print(
        f"Written reviews: {written}"
    )

    print(
        f"Structured-only reviews: "
        f"{structured}"
    )

    print(
        f"Rating-only reviews: "
        f"{rating_only}"
    )

    # ========================================================
    # IMAGES
    # ========================================================

    reviews_with_images = sum(
        1
        for r in reviews
        if r["has_images"] == "TRUE"
    )

    print(
        f"Reviews with images: "
        f"{reviews_with_images}"
    )

    # ========================================================
    # OWNER RESPONSES
    # ========================================================

    responses = sum(
        1
        for r in reviews
        if r["owner_response"].strip()
    )

    print(
        f"Reviews with owner response: "
        f"{responses}"
    )

    # ========================================================
    # RATINGS
    # ========================================================

    rating_counts = {}

    for review in reviews:

        rating = review["rating"]

        rating_counts[rating] = (
            rating_counts.get(
                rating,
                0
            ) + 1
        )

    print(
        "\nOverall rating breakdown:"
    )

    for rating in sorted(
        rating_counts.keys(),
        key=lambda x: float(x)
        if x != ""
        else 0,
        reverse=True
    ):

        print(
            f"  {rating} stars: "
            f"{rating_counts[rating]}"
        )

    # ========================================================
    # STRUCTURED RATINGS
    # ========================================================

    for field, label in [
        (
            "food_rating",
            "Food"
        ),
        (
            "service_rating",
            "Service"
        ),
        (
            "atmosphere_rating",
            "Atmosphere"
        ),
    ]:

        values = []

        for review in reviews:

            value = review[field]

            if value == "":
                continue

            try:
                values.append(
                    float(value)
                )
            except (
                ValueError,
                TypeError
            ):
                pass

        if values:

            average = (
                sum(values)
                / len(values)
            )

            print(
                f"Average {label} rating: "
                f"{average:.2f}"
            )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # GOOGLE MAPS DATA ID
    # ========================================================

    data_id = (
        "0x487605f1a33f49ef:0xec93b56f817231b6"
    )

    print("=" * 70)

    print(
        "GAIL'S BAKERY SOUTHBANK"
    )

    print(
        "GOOGLE MAPS REVIEW SCRAPER"
    )

    print("=" * 70)

    print(
        f"Start date: {START_DATE}"
    )

    print(
        f"End date:   {END_DATE}"
    )

    print(
        f"Output:     {OUTPUT_FILE}"
    )

    print(
        "\nStarting scraper..."
    )

    # ========================================================
    # FETCH
    # ========================================================

    all_reviews = fetch_reviews(
        data_id
    )

    # ========================================================
    # WRITE
    # ========================================================

    write_reviews_to_csv(
        all_reviews,
        OUTPUT_FILE
    )

    # ========================================================
    # STATISTICS
    # ========================================================

    print_statistics(
        all_reviews
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print("\n")
    print("=" * 70)

    print(
        "SCRAPING COMPLETE"
    )

    print("=" * 70)

    print(
        f"Total reviews collected: "
        f"{len(all_reviews)}"
    )

    print(
        f"CSV saved to: "
        f"{OUTPUT_FILE}"
    )