import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_listings():
    """Load mock thrift listings from the data folder."""
    listings_path = DATA_DIR / "listings.json"

    with listings_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_example_wardrobe():
    """Return a sample wardrobe for testing outfit suggestions later."""
    return {
        "items": [
            {
                "id": "W001",
                "name": "Baggy light wash jeans",
                "category": "bottom",
                "colors": ["light blue"],
                "style_tags": ["baggy", "denim", "streetwear"]
            },
            {
                "id": "W002",
                "name": "White chunky sneakers",
                "category": "shoes",
                "colors": ["white"],
                "style_tags": ["chunky", "casual", "sporty"]
            },
            {
                "id": "W003",
                "name": "Black lace-up boots",
                "category": "shoes",
                "colors": ["black"],
                "style_tags": ["edgy", "grunge", "classic"]
            },
            {
                "id": "W004",
                "name": "Gray oversized hoodie",
                "category": "top",
                "colors": ["gray"],
                "style_tags": ["cozy", "oversized", "streetwear"]
            },
            {
                "id": "W005",
                "name": "Black mini skirt",
                "category": "bottom",
                "colors": ["black"],
                "style_tags": ["minimal", "night-out", "layering"]
            }
        ]
    }


def get_empty_wardrobe():
    """Return an empty wardrobe structure."""
    return {"items": []}
