# FitFindr: Multi-Tool AI Agent

## Project Overview

FitFindr is a thrift-shopping AI agent that interprets a natural-language request, searches mock secondhand listings, chooses a matching item, suggests an outfit using the user's wardrobe, and creates a final fit card. The project is built around a conditional planning loop so the agent only runs later tools when earlier steps succeed.

## What This Project Demonstrates

This project demonstrates a multi-tool agent with three required tools: listing search, outfit suggestion, and fit card creation. It also includes an enhancement planning tool, `interpret_query`, that uses Groq when available to convert natural-language requests into structured search parameters. The project demonstrates a planning loop, session state management, graceful error handling, pytest tests, and a Gradio UI in `app.py`.

## Tool Inventory

| Tool Name | Function Signature | Inputs/Types | Output Type | Purpose | Failure Behavior |
| --- | --- | --- | --- | --- | --- |
| Query Interpreter Enhancement | `interpret_query(user_query)` | `user_query`: `str` | `dict` with `description`, `size`, `max_price`, `style` | Planning/query interpretation tool that converts natural language into search parameters before listing search. | Uses deterministic fallback parsing if Groq is unavailable, returns safe defaults, and never crashes the agent. |
| Search Listings | `search_listings(description, size, max_price)` | `description`: `str`, `size`: `str` or `None`, `max_price`: `float` or `None` | `list[dict]` | Searches `data/listings.json` for thrift listings using keyword overlap, optional size filter, and optional price filter. | Returns `[]` for empty descriptions, load errors, no matches, or unusable listing data. Skips broken listings. |
| Suggest Outfit | `suggest_outfit(new_item, wardrobe)` | `new_item`: `dict`, `wardrobe`: `dict` | `str` | Suggests how to style the selected thrift item with wardrobe pieces. | Returns a non-empty fallback string if wardrobe is empty, Groq is unavailable, API calls fail, or item fields are missing. |
| Create Fit Card | `create_fit_card(outfit, new_item)` | `outfit`: `str`, `new_item`: `dict` | `str` | Formats the selected item and outfit suggestion into a final fit card. | Returns a clear error string for an empty outfit. Uses safe defaults for missing item fields and fallback text if Groq is unavailable. |

`search_listings`, `suggest_outfit`, and `create_fit_card` are the required project tools. `interpret_query` is an enhancement planning tool that runs before the required tools.

## Planning Loop

`run_agent(user_query, size=None, max_price=None, wardrobe=None)` follows this exact conditional flow:

1. Receive the user query.
2. Initialize the session dictionary.
3. Call `interpret_query(user_query)`.
4. Store the parsed result in `session["parsed_query"]`.
5. Use `parsed_query["description"]` as the search description.
6. Use the explicit `size` argument if provided, otherwise use `parsed_query["size"]`.
7. Use the explicit `max_price` argument if provided, otherwise use `parsed_query["max_price"]`.
8. Call `search_listings(description, effective_size, effective_max_price)`.
9. Store results in `session["search_results"]`.
10. If results are empty, set `session["error"]`, add an early-stop step, and return the session immediately.
11. If results exist, set `session["selected_item"] = results[0]`.
12. Call `suggest_outfit(session["selected_item"], wardrobe)`.
13. Store the result in `session["outfit_suggestion"]`.
14. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
15. Store the result in `session["fit_card"]`.
16. Return the full session.

The agent is conditional. It does not call `suggest_outfit` or `create_fit_card` when search returns no results.

## Architecture

```text
User Query
    |
    v
interpret_query()
    |
    v
search_listings()
    |
    +--> No results -> set error and stop early
    |
    v
suggest_outfit()
    |
    v
create_fit_card()
    |
    v
Final session and UI output
```

## State Management

The agent returns one session dictionary with these fields:

| Field | Meaning |
| --- | --- |
| `user_query` | The original user request. |
| `parsed_query` | The dictionary returned by `interpret_query`, containing `description`, `size`, `max_price`, and `style`. |
| `search_results` | The list returned by `search_listings`. |
| `selected_item` | The first search result chosen for styling, or `None` if search fails. |
| `outfit_suggestion` | The string returned by `suggest_outfit`, or `None` if search fails before this tool runs. |
| `fit_card` | The string returned by `create_fit_card`, or `None` if search fails before this tool runs. |
| `error` | A helpful error message when the workflow cannot continue. |
| `steps` | A list of planning-loop steps completed by the agent. |

State passes between tools in order: `interpret_query` creates `parsed_query`, the parsed `description`/`size`/`max_price` are passed into `search_listings`, `search_results[0]` becomes `selected_item`, `selected_item` is passed into `suggest_outfit`, and `outfit_suggestion` is passed into `create_fit_card`.

## Error Handling Strategy

Query interpretation failure: `interpret_query` returns deterministic fallback values using the original query as the description and `None` for missing size, price, or style.

No listings found: `search_listings` returns `[]`. `run_agent` stores a helpful error, records that it stopped early, and returns before outfit or fit card generation.

Empty wardrobe: `suggest_outfit` returns general styling advice using the thrift item as the main piece.

Empty outfit string: `create_fit_card` returns a clear message explaining that the fit card could not be created because the outfit suggestion is empty.

LLM/API unavailable: Groq is only used when `GROQ_API_KEY` exists. If the key is missing, the package is unavailable, or the API call fails, the interpreter and styling tools return deterministic fallback outputs.

Missing listing fields: search skips unusable listings when needed. Styling and fit card generation use safe defaults such as `this thrift find`, `Unknown price`, `Unknown platform`, and `Unknown condition`.

Concrete examples from tests:

- `test_search_empty_results` searches for `"designer ballgown"` with size `"XXS"` and max price `5`; the expected result is `[]`.
- `test_interpret_query_fallback_basic` verifies that the fallback parser extracts `"vintage graphic tee"`, max price `30.0`, and style `"vintage"` without live Groq.
- `test_run_agent_uses_parsed_query_when_size_and_price_not_explicit` verifies that parsed size and price are passed into `search_listings`.
- `test_agent_stops_on_no_results` verifies that an impossible query sets `session["error"]`, leaves `selected_item` as `None`, and does not generate an outfit suggestion or fit card.
- `test_create_fit_card_empty_outfit` verifies that an empty outfit returns a non-empty explanation instead of a blank card.

## How to Run

Mac/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

To see the same agent workflow from the command line instead of the Gradio UI, run:

```bash
python agent.py
```

## Environment Variables

Create a `.env` file from `.env.example` and set:

```text
GROQ_API_KEY=your_key_here
```

Fallback outputs still work without a Groq key. Without `GROQ_API_KEY`, `suggest_outfit` and `create_fit_card` use deterministic local fallback text.

## How to Test

```bash
pytest tests/
```

If using the local virtual environment:

```bash
.venv/bin/pytest tests/
```

Current verified result:

```text
9 passed
```

## Demo Video Script

1. Introduce FitFindr as a thrift-shopping multi-tool AI agent.
2. Show the happy path: search for `"I want a vintage graphic tee under 30 dollars"`, then explain that `interpret_query` extracts the search parameters before the required tools run.
3. Explain state passing: `parsed_query` goes into search, `selected_item` from search goes into `suggest_outfit`, and `outfit_suggestion` goes into `create_fit_card`.
4. Trigger a no-results failure with an impossible query such as `"designer ballgown"`, size `"XXS"`, max price `5`.
5. Show the graceful error and point out that outfit/card generation did not run.
6. Mention that pytest tests and `planning.md` document the required workflow and error handling.

## AI Usage

Used Codex to implement `search_listings` from the `planning.md` specs; reviewed filters, keyword scoring, missing field handling, and empty result behavior.

Used Codex to implement `run_agent` from the architecture diagram; verified the no-results branch stops before outfit/card generation.

Used Codex to create pytest tests that avoid live Groq calls by using fallback behavior and monkeypatching LLM helper calls where needed.

Used Codex to add `interpret_query` as a Groq-powered planning enhancement and then update tests so parsed-query routing remains verified without live LLM calls.

## Spec Reflection

One way `planning.md` helped: it made the planning loop explicit before implementation, especially the rule that later tools must not run if search fails.

One way implementation diverged and why: `planning.md` originally showed the agent searching directly with the raw user query. The implementation now adds `interpret_query` before search so natural-language requests like `"I need a y2k jacket under 50 bucks"` become structured search parameters.
