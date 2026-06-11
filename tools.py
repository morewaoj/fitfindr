import os
import re

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return False

from utils.data_loader import load_listings


MODEL_NAME = "llama-3.3-70b-versatile"


def _clean_words(text):
    if not isinstance(text, str):
        return []

    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if len(word) > 1]


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _listing_search_text(listing):
    parts = []

    for field in ["title", "description", "category", "brand", "platform"]:
        value = listing.get(field, "")
        if isinstance(value, str):
            parts.append(value)

    for field in ["style_tags", "colors"]:
        values = _safe_list(listing.get(field, []))
        parts.extend(str(value) for value in values)

    return " ".join(parts).lower()


def _keyword_overlap(description, listing):
    search_words = set(_clean_words(description))
    listing_words = set(_clean_words(_listing_search_text(listing)))

    if not search_words:
        return 0

    return len(search_words.intersection(listing_words))


def _get_groq_client():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    try:
        from groq import Groq

        return Groq(api_key=api_key)
    except Exception:
        return None


def _call_groq(prompt, temperature):
    client = _get_groq_client()

    if client is None:
        return ""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are FitFindr, a concise thrift-styling assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=220
        )
        content = response.choices[0].message.content

        if isinstance(content, str):
            return content.strip()
        return ""
    except Exception:
        return ""


def search_listings(description, size, max_price):
    """Search mock thrift listings by description, optional size, and optional price."""
    if not isinstance(description, str) or not description.strip():
        return []

    try:
        listings = load_listings()
    except Exception:
        return []

    if not isinstance(listings, list):
        return []

    matches = []

    for listing in listings:
        if not isinstance(listing, dict):
            continue

        try:
            relevance = _keyword_overlap(description, listing)

            if relevance == 0:
                continue

            if size:
                listing_size = str(listing.get("size", "")).strip().lower()
                requested_size = str(size).strip().lower()

                if listing_size != requested_size:
                    continue

            if max_price is not None:
                price = float(listing.get("price"))

                if price > float(max_price):
                    continue

            matches.append((relevance, listing))
        except Exception:
            continue

    matches.sort(key=lambda match: match[0], reverse=True)
    return [listing for relevance, listing in matches]


def _item_title(new_item):
    if isinstance(new_item, dict):
        title = new_item.get("title") or new_item.get("name")
        if title:
            return str(title)
    return "this thrift find"


def _item_style_text(new_item):
    if not isinstance(new_item, dict):
        return "versatile"

    tags = _safe_list(new_item.get("style_tags", []))
    category = new_item.get("category", "")
    colors = _safe_list(new_item.get("colors", []))
    parts = tags + [category] + colors
    clean_parts = [str(part) for part in parts if part]

    if clean_parts:
        return ", ".join(clean_parts)
    return "versatile"


def _wardrobe_items(wardrobe):
    if not isinstance(wardrobe, dict):
        return []
    return _safe_list(wardrobe.get("items", []))


def _item_name(item):
    if not isinstance(item, dict):
        return ""
    return str(item.get("name") or item.get("title") or "").strip()


def _choose_wardrobe_pieces(wardrobe):
    items = [item for item in _wardrobe_items(wardrobe) if isinstance(item, dict)]
    named_items = [item for item in items if _item_name(item)]

    bottoms = [
        item for item in named_items
        if str(item.get("category", "")).lower() in ["bottom", "bottoms", "pants", "skirt"]
    ]
    shoes = [
        item for item in named_items
        if str(item.get("category", "")).lower() in ["shoes", "shoe", "boots", "sneakers"]
    ]
    tops = [
        item for item in named_items
        if str(item.get("category", "")).lower() in ["top", "tops", "shirt", "hoodie", "sweater"]
    ]

    selected = []

    for group in [bottoms, shoes, tops, named_items]:
        for item in group:
            if item not in selected:
                selected.append(item)
            if len(selected) >= 2:
                return selected

    return selected


def _fallback_outfit(new_item, wardrobe):
    title = _item_title(new_item)
    style_text = _item_style_text(new_item)
    selected_items = _choose_wardrobe_pieces(wardrobe)

    if not selected_items:
        return (
            f"Style {title} as the main piece with simple basics you already own. "
            f"Because it has a {style_text} feel, pair it with neutral bottoms, comfortable shoes, "
            "and one matching accessory so the outfit feels intentional."
        )

    item_names = [_item_name(item) for item in selected_items]

    if len(item_names) == 1:
        wardrobe_text = item_names[0]
    else:
        wardrobe_text = f"{item_names[0]} and {item_names[1]}"

    return (
        f"Wear {title} with your {wardrobe_text}. "
        f"The thrifted item has a {style_text} feel, so these wardrobe pieces keep the outfit balanced, "
        "easy to wear, and true to your existing style."
    )


def suggest_outfit(new_item, wardrobe):
    """Suggest an outfit using the selected item and the user's wardrobe."""
    if not isinstance(new_item, dict) or not new_item:
        return "I could not style this item because the selected listing is missing."

    fallback = _fallback_outfit(new_item, wardrobe)
    wardrobe_items = _wardrobe_items(wardrobe)

    prompt = (
        "Create one short outfit suggestion for a thrift shopper.\n"
        f"New thrift item: {new_item}\n"
        f"User wardrobe: {wardrobe_items}\n"
        "Mention the thrift item and one or two wardrobe items if available. "
        "Keep it beginner-friendly and under 80 words."
    )
    groq_result = _call_groq(prompt, temperature=0.5)

    if groq_result:
        return groq_result

    return fallback


def _format_price(value):
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "Unknown price"


def _fallback_fit_card(outfit, new_item):
    title = _item_title(new_item)
    price = _format_price(new_item.get("price")) if isinstance(new_item, dict) else "Unknown price"
    platform = str(new_item.get("platform", "Unknown platform")) if isinstance(new_item, dict) else "Unknown platform"
    condition = str(new_item.get("condition", "Unknown condition")) if isinstance(new_item, dict) else "Unknown condition"

    return (
        "FIT CARD\n"
        f"Item: {title}\n"
        f"Price: {price}\n"
        f"Platform: {platform}\n"
        f"Condition: {condition}\n"
        f"Outfit: {outfit}\n"
        "Why it works: This thrift find can work with the outfit above because it connects the new item "
        "to pieces the shopper can already wear."
    )


def create_fit_card(outfit, new_item):
    """Create a final fit card for the selected item and outfit suggestion."""
    if not isinstance(outfit, str) or not outfit.strip():
        return "Fit card could not be created because the outfit suggestion is empty."

    safe_outfit = outfit.strip()
    fallback = _fallback_fit_card(safe_outfit, new_item)

    prompt = (
        "Create a concise thrift fashion fit card using this exact information.\n"
        f"New thrift item: {new_item}\n"
        f"Outfit suggestion: {safe_outfit}\n"
        "Include item, price, platform, condition, outfit, and why it works. "
        "Use a fun but clear caption style."
    )
    groq_result = _call_groq(prompt, temperature=0.9)

    if groq_result:
        return groq_result

    return fallback
