# FitFindr: Multi-Tool AI Agent

## Project Overview

FitFindr is a thrift-shopping AI agent that searches mock secondhand listings, chooses a matching item, suggests an outfit using the user's wardrobe, and creates a final fit card. The project is built around a conditional planning loop so the agent only runs later tools when earlier steps succeed.

## What This Project Demonstrates

This project demonstrates a multi-tool agent with three required tools: listing search, outfit suggestion, and fit card creation. It also demonstrates a planning loop, session state management, graceful error handling, pytest tests, and a Gradio UI dependency/entry point. The current `app.py` file is still a placeholder, so the verified working interface right now is the Python agent and tests.

## Tool Inventory

| Tool Name | Function Signature | Inputs/Types | Output Type | Purpose | Failure Behavior |
| --- | --- | --- | --- | --- | --- |
| Search Listings | `search_listings(description, size, max_price)` | `description`: `str`, `size`: `str` or `None`, `max_price`: `float` or `None` | `list[dict]` | Searches `data/listings.json` for thrift listings using keyword overlap, optional size filter, and optional price filter. | Returns `[]` for empty descriptions, load errors, no matches, or unusable listing data. Skips broken listings. |
| Suggest Outfit | `suggest_outfit(new_item, wardrobe)` | `new_item`: `dict`, `wardrobe`: `dict` | `str` | Suggests how to style the selected thrift item with wardrobe pieces. | Returns a non-empty fallback string if wardrobe is empty, Groq is unavailable, API calls fail, or item fields are missing. |
| Create Fit Card | `create_fit_card(outfit, new_item)` | `outfit`: `str`, `new_item`: `dict` | `str` | Formats the selected item and outfit suggestion into a final fit card. | Returns a clear error string for an empty outfit. Uses safe defaults for missing item fields and fallback text if Groq is unavailable. |

## Planning Loop

`run_agent(user_query, size=None, max_price=None, wardrobe=None)` follows this exact conditional flow:

1. Receive the user query.
2. Initialize the session dictionary.
3. Call `search_listings(user_query, size, max_price)`.
4. Store results in `session["search_results"]`.
5. If results are empty, set `session["error"]`, add an early-stop step, and return the session immediately.
6. If results exist, set `session["selected_item"] = results[0]`.
7. Call `suggest_outfit(session["selected_item"], wardrobe)`.
8. Store the result in `session["outfit_suggestion"]`.
9. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
10. Store the result in `session["fit_card"]`.
11. Return the full session.

The agent is conditional. It does not call `suggest_outfit` or `create_fit_card` when search returns no results.

## State Management

The agent returns one session dictionary with these fields:

| Field | Meaning |
| --- | --- |
| `user_query` | The original user request. |
| `search_results` | The list returned by `search_listings`. |
| `selected_item` | The first search result chosen for styling, or `None` if search fails. |
| `outfit_suggestion` | The string returned by `suggest_outfit`, or `None` if search fails before this tool runs. |
| `fit_card` | The string returned by `create_fit_card`, or `None` if search fails before this tool runs. |
| `error` | A helpful error message when the workflow cannot continue. |
| `steps` | A list of planning-loop steps completed by the agent. |

## Error Handling Strategy

No listings found: `search_listings` returns `[]`. `run_agent` stores a helpful error, records that it stopped early, and returns before outfit or fit card generation.

Empty wardrobe: `suggest_outfit` returns general styling advice using the thrift item as the main piece.

Empty outfit string: `create_fit_card` returns a clear message explaining that the fit card could not be created because the outfit suggestion is empty.

LLM/API unavailable: Groq is only used when `GROQ_API_KEY` exists. If the key is missing, the package is unavailable, or the API call fails, the tools return deterministic fallback text.

Missing listing fields: search skips unusable listings when needed. Styling and fit card generation use safe defaults such as `this thrift find`, `Unknown price`, `Unknown platform`, and `Unknown condition`.

Concrete examples from tests:

- `test_search_empty_results` searches for `"designer ballgown"` with size `"XXS"` and max price `5`; the expected result is `[]`.
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

Current note: `app.py` is present as the Gradio entry point but does not yet launch a UI. To see the implemented agent workflow from the command line, run:

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
6 passed
```

## Demo Video Script

1. Introduce FitFindr as a thrift-shopping multi-tool AI agent.
2. Show the happy path: search for `"vintage graphic tee"` with size `"M"` and max price `30`, then explain that all three tools run.
3. Explain state passing: `selected_item` from search goes into `suggest_outfit`, and `outfit_suggestion` goes into `create_fit_card`.
4. Trigger a no-results failure with an impossible query such as `"designer ballgown"`, size `"XXS"`, max price `5`.
5. Show the graceful error and point out that outfit/card generation did not run.
6. Mention that pytest tests and `planning.md` document the required workflow and error handling.

## AI Usage

Used Codex to implement `search_listings` from the `planning.md` specs; reviewed filters, keyword scoring, missing field handling, and empty result behavior.

Used Codex to implement `run_agent` from the architecture diagram; verified the no-results branch stops before outfit/card generation.

Used Codex to create pytest tests that avoid live Groq calls by using fallback behavior and monkeypatching LLM helper calls where needed.

## Spec Reflection

One way `planning.md` helped: it made the planning loop explicit before implementation, especially the rule that later tools must not run if search fails.

One way implementation diverged and why: `planning.md` originally showed `outfit_suggestion` and `fit_card` as empty strings in the initial session. The implementation now uses `None` for those fields before the tools run, because the tests verify that no-results workflows leave them unset. This makes the early-stop behavior easier to prove.
