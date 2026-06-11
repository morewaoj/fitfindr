from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_example_wardrobe


def _new_session(user_query):
    return {
        "user_query": user_query,
        "search_results": [],
        "selected_item": None,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": "",
        "steps": []
    }


def run_agent(user_query, size=None, max_price=None, wardrobe=None):
    session = _new_session(user_query)
    session["steps"].append("Received user query.")

    if wardrobe is None:
        wardrobe = {"items": []}

    results = search_listings(user_query, size, max_price)
    session["search_results"] = results
    session["steps"].append("Searched thrift listings.")

    if not results:
        session["error"] = (
            "I could not find any matching thrift listings. "
            "Try a different description, size, or price limit."
        )
        session["steps"].append("Stopped early because search returned no results.")
        return session

    session["selected_item"] = results[0]
    selected_title = session["selected_item"].get("title", "the first matching item")
    session["steps"].append(f"Selected item: {selected_title}.")

    outfit_suggestion = suggest_outfit(session["selected_item"], wardrobe)
    session["outfit_suggestion"] = outfit_suggestion
    session["steps"].append("Created outfit suggestion.")

    fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    session["fit_card"] = fit_card
    session["steps"].append("Created fit card.")

    return session


if __name__ == "__main__":
    print("Happy path example")
    happy_session = run_agent(
        user_query="vintage graphic tee",
        size="M",
        max_price=30,
        wardrobe=get_example_wardrobe()
    )
    print(happy_session)

    print("\nNo-results example")
    no_results_session = run_agent(
        user_query="silver astronaut cape",
        size="XS",
        max_price=5,
        wardrobe=get_example_wardrobe()
    )
    print(no_results_session)
