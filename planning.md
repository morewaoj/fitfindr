# FitFindr Planning Document

## Project Summary

FitFindr is a thrift-shopping multi-tool AI agent that helps a user find a secondhand clothing item and style it with pieces they already own. The agent searches mock thrift listings first, stops early if there are no matching results, and only creates an outfit suggestion and fit card when a real listing is found.

## A Complete Interaction

Example user message:

```text
I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.
```

Initial session state:

```python
session = {
    "user_query": "I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.",
    "parsed_query": None,
    "search_results": [],
    "selected_item": None,
    "outfit_suggestion": "",
    "fit_card": "",
    "error": "",
    "steps": []
}
```

Step 1: The planning loop receives the query and calls `interpret_query`.

```python
interpret_query(
    "I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers."
)
```

Sample successful output:

```python
{
    "description": "vintage graphic tee",
    "size": "M",
    "max_price": 30.0,
    "style": "vintage"
}
```

State update:

```python
session["parsed_query"] = parsed_query
session["steps"].append("Received user query.")
session["steps"].append("Interpreted user query using planning tool.")
```

Step 2: The planning loop prepares search inputs from the parsed query.

```python
description = parsed_query["description"]
size = parsed_query["size"]
max_price = parsed_query["max_price"]
wardrobe = {
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
        }
    ]
}
```

Step 3: The planning loop calls `search_listings`.

```python
search_listings(
    description="vintage graphic tee",
    size="M",
    max_price=30.0
)
```

Sample successful output:

```python
[
    {
        "id": "L001",
        "title": "Vintage Graphic Tee",
        "description": "Soft black band-style tee with faded front print.",
        "category": "top",
        "style_tags": ["vintage", "graphic", "casual"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black", "white"],
        "brand": "Thread Archive",
        "platform": "Depop"
    }
]
```

State update:

```python
session["search_results"] = search_results
session["selected_item"] = search_results[0]
session["steps"].append("Found matching thrift listings.")
session["steps"].append("Selected the first matching item.")
```

Step 4: Since results exist, the planning loop calls `suggest_outfit`.

```python
suggest_outfit(
    new_item={
        "id": "L001",
        "title": "Vintage Graphic Tee",
        "description": "Soft black band-style tee with faded front print.",
        "category": "top",
        "style_tags": ["vintage", "graphic", "casual"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black", "white"],
        "brand": "Thread Archive",
        "platform": "Depop"
    },
    wardrobe=wardrobe
)
```

Sample successful output:

```text
Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.
```

State update:

```python
session["outfit_suggestion"] = outfit_suggestion
session["steps"].append("Created an outfit suggestion using the selected item and wardrobe.")
```

Step 5: The planning loop calls `create_fit_card`.

```python
create_fit_card(
    outfit="Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.",
    new_item={
        "id": "L001",
        "title": "Vintage Graphic Tee",
        "description": "Soft black band-style tee with faded front print.",
        "category": "top",
        "style_tags": ["vintage", "graphic", "casual"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black", "white"],
        "brand": "Thread Archive",
        "platform": "Depop"
    }
)
```

Sample successful output:

```text
FIT CARD
Item: Vintage Graphic Tee
Price: $24.00
Platform: Depop
Condition: good
Outfit: Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.
Why it works: This thrift find fits the budget, matches the requested size, and pairs with pieces already in the wardrobe.
```

State update:

```python
session["fit_card"] = fit_card
session["steps"].append("Created final fit card.")
```

Final response:

```text
I found a Vintage Graphic Tee for $24.00 on Depop.

Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.

FIT CARD
Item: Vintage Graphic Tee
Price: $24.00
Platform: Depop
Condition: good
Outfit: Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.
Why it works: This thrift find fits the budget, matches the requested size, and pairs with pieces already in the wardrobe.
```

## Tool Specifications

### interpret_query(user_query: str) -> dict

Purpose: Interpret the user's natural-language thrift request before search and convert it into structured search parameters.

Inputs:

- `user_query`: The original user request, such as `"I need a y2k jacket under 50 bucks"`.

Output:

```python
{
    "description": str,
    "size": str | None,
    "max_price": float | None,
    "style": str | None
}
```

Success behavior:

- Use Groq `llama-3.3-70b-versatile` when `GROQ_API_KEY` exists.
- Return a validated dictionary with exactly `description`, `size`, `max_price`, and `style`.
- Extract size when the user says something like `"size L"`.
- Extract max price when the user says something like `"under 30 dollars"` or `"under 50 bucks"`.
- Extract a known style such as `vintage`, `y2k`, or `workwear`.

Failure behavior:

- If Groq is unavailable, use a deterministic fallback parser.
- If parsing fails, return the original query as `description` and `None` for `size`, `max_price`, and `style`.
- Do not raise an uncaught exception to the agent.

`interpret_query` is an enhancement planning/query interpretation tool. The required project tools remain `search_listings`, `suggest_outfit`, and `create_fit_card`.

### search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]

Purpose: Search the mock thrift listing dataset for items that match the user's item description, optional size, and optional maximum price.

Inputs:

- `description`: A string describing the item the user wants, such as `"vintage graphic tee"`.
- `size`: A string size filter, such as `"M"`, or `None` when the user did not provide a size.
- `max_price`: A float price limit, such as `30.0`, or `None` when the user did not provide a budget.

Output: A list of listing dictionaries. Each dictionary should contain listing fields such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Success behavior:

- Load listings from `data/listings.json`.
- Match listings by checking whether words from `description` appear in the listing title, description, category, or style tags.
- If `size` is provided, only include listings with the same size.
- If `max_price` is provided, only include listings with `price <= max_price`.
- Return all matching listings as a list.
- Return an empty list when no listings match.

Failure behavior:

- If the data file cannot be loaded, return an empty list.
- If a listing is missing a field, skip that listing instead of crashing.
- If `description` is empty or not a string, return an empty list.
- Do not raise an uncaught exception to the agent.

### suggest_outfit(new_item: dict, wardrobe: dict) -> str

Purpose: Suggest a simple outfit that pairs the selected thrift item with the user's existing wardrobe.

Inputs:

- `new_item`: The selected listing dictionary returned by `search_listings`.
- `wardrobe`: A dictionary with an `"items"` list. Each wardrobe item should include `id`, `name`, `category`, `colors`, and `style_tags`.

Output: A string containing a short outfit suggestion.

Success behavior:

- Use the selected item and wardrobe pieces to create a readable outfit suggestion.
- Prefer wardrobe items with compatible categories and style tags.
- Mention the selected thrift item by title.
- Mention at least one wardrobe item when the wardrobe is not empty.
- Return one clear paragraph.

Failure behavior:

- If `new_item` is missing required fields, return an error message string that explains the item could not be styled.
- If `wardrobe` is missing or has no items, return a graceful suggestion using only the new item.
- If a Groq LLM/API call is used later and fails, return a simple non-LLM fallback outfit suggestion.
- Do not raise an uncaught exception to the agent.

### create_fit_card(outfit: str, new_item: dict) -> str

Purpose: Format the final shopping result and outfit suggestion into a user-friendly fit card.

Inputs:

- `outfit`: The outfit suggestion string returned by `suggest_outfit`.
- `new_item`: The selected listing dictionary returned by `search_listings`.

Output: A formatted string fit card.

Success behavior:

- Include the selected item's title.
- Include price, platform, and condition when available.
- Include the outfit suggestion.
- Include a short "why it works" explanation.
- Return a single formatted string that can be shown directly to the user.

Failure behavior:

- If `outfit` is empty, return a graceful error message string instead of a blank card.
- If `new_item` is missing fields, use safe defaults such as `"Unknown item"`, `"Unknown platform"`, or `"Unknown condition"`.
- Do not raise an uncaught exception to the agent.

## Planning Loop

Exact conditional logic:

1. Receive the user query.
2. Save the original query in `session["user_query"]`.
3. Add `"Received user query."` to `session["steps"]`.
4. Call `interpret_query(user_query)`.
5. Store the result in `session["parsed_query"]`.
6. Add `"Interpreted user query using planning tool."` to `session["steps"]`.
7. Set `description = parsed_query["description"]`.
8. Set `effective_size` to the explicit `size` argument if provided, otherwise `parsed_query["size"]`.
9. Set `effective_max_price` to the explicit `max_price` argument if provided, otherwise `parsed_query["max_price"]`.
10. Call `search_listings(description, effective_size, effective_max_price)`.
11. If the search results list is empty, set `session["error"] = "No matching listings found."`.
12. If the search results list is empty, add `"Stopped because search returned no results."` to `session["steps"]`.
13. If the search results list is empty, return the session immediately.
14. If results exist, set `session["search_results"] = search_results`.
15. If results exist, set `session["selected_item"] = search_results[0]`.
16. If results exist, add `"Selected the first matching listing."` to `session["steps"]`.
17. Call `suggest_outfit(session["selected_item"], wardrobe)`.
18. Store the result in `session["outfit_suggestion"]`.
19. Add `"Created outfit suggestion."` to `session["steps"]`.
20. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
21. Store the result in `session["fit_card"]`.
22. Add `"Created fit card."` to `session["steps"]`.
23. Return the session.

Later tools must not run if search fails. If `search_listings` returns an empty list, the agent must not call `suggest_outfit` and must not call `create_fit_card`.

## State Management

The agent manages session state with one dictionary.

```python
session = {
    "user_query": "",
    "parsed_query": None,
    "search_results": [],
    "selected_item": None,
    "outfit_suggestion": None,
    "fit_card": None,
    "error": "",
    "steps": []
}
```

State fields:

- `user_query`: The original user request.
- `parsed_query`: The dictionary returned by `interpret_query`, including `description`, `size`, `max_price`, and `style`.
- `search_results`: A list of listings returned by `search_listings`.
- `selected_item`: The listing chosen for styling. The first matching result will be used in the basic implementation.
- `outfit_suggestion`: The text returned by `suggest_outfit`.
- `fit_card`: The final formatted text returned by `create_fit_card`.
- `error`: A user-readable error message. Empty string means no error.
- `steps`: A list of strings showing what the planning loop did.

## Architecture

```text
User query
    |
    v
Planning loop
    |
    v
interpret_query(user_query)
    |
    v
Set session["parsed_query"]
    |
    v
search_listings(description, effective_size, effective_max_price)
    |
    +--> No results or search error
    |       |
    |       v
    |   Set session["error"]
    |       |
    |       v
    |   Return early
    |
    +--> Results found
            |
            v
        Set session["search_results"]
            |
            v
        Set session["selected_item"]
            |
            v
        suggest_outfit(selected_item, wardrobe)
            |
            v
        Set session["outfit_suggestion"]
            |
            v
        create_fit_card(outfit_suggestion, selected_item)
            |
            v
        Set session["fit_card"]
            |
            v
        Final response
```

## Error Handling Strategy

| Tool | Failure Mode | Agent Response | Continue or Stop |
| --- | --- | --- | --- |
| `interpret_query` | Groq unavailable or parsing fails | Use deterministic fallback with original query as `description` and `None` for missing fields. | Continue |
| `interpret_query` | Invalid parsed fields | Validate output, normalize size/style, and replace invalid values with safe defaults. | Continue |
| `search_listings` | No listings found | Set `session["error"] = "No matching listings found."` and add a stop message to `session["steps"]`. | Stop |
| `search_listings` | Listing data file cannot be loaded | Return an empty list, set `session["error"] = "No matching listings found."`, and stop early. | Stop |
| `search_listings` | Listing is missing fields | Skip the broken listing and keep checking other listings. | Continue |
| `search_listings` | Empty or invalid description | Return an empty list, set `session["error"] = "No matching listings found."`, and stop early. | Stop |
| `suggest_outfit` | Empty wardrobe | Return a graceful outfit suggestion using only the selected thrift item. | Continue |
| `suggest_outfit` | Missing fields in `new_item` | Return an error-style suggestion string explaining that the item could not be styled. | Continue |
| `suggest_outfit` | LLM/API failure | Return a simple non-LLM fallback outfit suggestion. | Continue |
| `create_fit_card` | Empty outfit string | Return a graceful error message string instead of a blank card. | Continue |
| `create_fit_card` | Missing fields in `new_item` | Use safe defaults for missing values and still build a card. | Continue |

## AI Tool Plan

Codex will be used phase by phase, with one clear goal per phase.

Phase 0: Inspect the repository. Verify current files, starter code, missing files, and project risks before editing.

Phase 1: Create the project skeleton. Verify the file tree, required dependency files, mock listing data, wardrobe schema, and placeholder files.

Phase 2: Complete `planning.md`. Verify that the plan includes all required tools, planning-loop conditions, state fields, error handling, and a complete walkthrough.

Phase 3: Implement `tools.py`. Verify each tool manually and with tests that do not call live LLMs.

Phase 4: Implement `agent.py`. Verify that the planning loop uses conditional logic, stores session state, stops early when search returns no results, and does not blindly call every tool.

Phase 5: Implement `app.py`. Verify that the app demonstrates the multi-step workflow through a simple interface.

Phase 6: Complete tests. Verify that tests cover successful search, no-results search, empty wardrobe handling, fit card formatting, and early stop behavior. Tests must not depend on live Groq calls.

Phase 7: Complete `README.md`. Verify that setup, environment variables, running the app, running tests, and project requirement coverage are instructor-ready.

## Complete Interaction Walkthrough

User query:

```text
I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.
```

The agent creates a new session:

```python
session = {
    "user_query": "I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.",
    "parsed_query": None,
    "search_results": [],
    "selected_item": None,
    "outfit_suggestion": None,
    "fit_card": None,
    "error": "",
    "steps": ["Received user query."]
}
```

Tool call 1:

```python
parsed_query = interpret_query(
    "I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers."
)
```

Tool 1 output:

```python
{
    "description": "vintage graphic tee",
    "size": "M",
    "max_price": 30.0,
    "style": "vintage"
}
```

State update:

```python
session["parsed_query"] = parsed_query
session["steps"].append("Interpreted user query using planning tool.")
```

The agent prepares search inputs:

```python
description = parsed_query["description"]
size = parsed_query["size"]
max_price = parsed_query["max_price"]
wardrobe = {
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
        }
    ]
}
```

Tool call 2:

```python
search_results = search_listings("vintage graphic tee", "M", 30.0)
```

Tool 2 output:

```python
[
    {
        "id": "L001",
        "title": "Vintage Graphic Tee",
        "description": "Soft black band-style tee with faded front print.",
        "category": "top",
        "style_tags": ["vintage", "graphic", "casual"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black", "white"],
        "brand": "Thread Archive",
        "platform": "Depop"
    }
]
```

Search result condition:

```python
if not search_results:
    session["error"] = "No matching listings found."
    session["steps"].append("Stopped because search returned no results.")
    return session
```

Because results exist, the agent continues:

```python
session["search_results"] = search_results
session["selected_item"] = search_results[0]
session["steps"].append("Selected the first matching listing.")
```

Tool call 2:

```python
outfit_suggestion = suggest_outfit(session["selected_item"], wardrobe)
```

Tool 2 output:

```text
Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.
```

State update:

```python
session["outfit_suggestion"] = outfit_suggestion
session["steps"].append("Created outfit suggestion.")
```

Tool call 3:

```python
fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

Tool 3 output:

```text
FIT CARD
Item: Vintage Graphic Tee
Price: $24.00
Platform: Depop
Condition: good
Outfit: Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.
Why it works: This thrift find fits the budget, matches the requested size, and pairs with pieces already in the wardrobe.
```

Final state:

```python
session = {
    "user_query": "I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.",
    "search_results": [
        {
            "id": "L001",
            "title": "Vintage Graphic Tee",
            "description": "Soft black band-style tee with faded front print.",
            "category": "top",
            "style_tags": ["vintage", "graphic", "casual"],
            "size": "M",
            "condition": "good",
            "price": 24.0,
            "colors": ["black", "white"],
            "brand": "Thread Archive",
            "platform": "Depop"
        }
    ],
    "selected_item": {
        "id": "L001",
        "title": "Vintage Graphic Tee",
        "description": "Soft black band-style tee with faded front print.",
        "category": "top",
        "style_tags": ["vintage", "graphic", "casual"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black", "white"],
        "brand": "Thread Archive",
        "platform": "Depop"
    },
    "outfit_suggestion": "Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.",
    "fit_card": "FIT CARD\nItem: Vintage Graphic Tee\nPrice: $24.00\nPlatform: Depop\nCondition: good\nOutfit: Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.\nWhy it works: This thrift find fits the budget, matches the requested size, and pairs with pieces already in the wardrobe.",
    "error": "",
    "steps": [
        "Received user query.",
        "Selected the first matching listing.",
        "Created outfit suggestion.",
        "Created fit card."
    ]
}
```

Final user-facing response:

```text
I found a Vintage Graphic Tee for $24.00 on Depop.

Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.

FIT CARD
Item: Vintage Graphic Tee
Price: $24.00
Platform: Depop
Condition: good
Outfit: Wear the Vintage Graphic Tee with your baggy light wash jeans and white chunky sneakers. The baggy jeans match the casual vintage feel, and the sneakers keep the outfit relaxed and easy to wear.
Why it works: This thrift find fits the budget, matches the requested size, and pairs with pieces already in the wardrobe.
```

## Stretch Features Not Implemented

- Price comparison across multiple resale platforms will not be implemented.
- Long-term style memory across sessions will not be implemented.
- Trend awareness from live fashion data or social media will not be implemented.
- Retry fallback for failed API calls will not be implemented.
