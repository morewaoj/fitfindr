import agent

from agent import run_agent
from tools import create_fit_card, interpret_query, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe


def test_search_returns_results():
    result = search_listings("vintage graphic tee", size="M", max_price=30)

    assert isinstance(result, list)
    assert len(result) > 0


def test_search_empty_results():
    result = search_listings("designer ballgown", size="XXS", max_price=5)

    assert result == []


def test_search_price_filter():
    result = search_listings("shirt", size=None, max_price=10)

    assert all(item["price"] <= 10 for item in result)


def test_suggest_outfit_empty_wardrobe(monkeypatch):
    monkeypatch.setattr("tools._call_groq", lambda prompt, temperature: "")
    listing = search_listings("vintage graphic tee", size="M", max_price=30)[0]

    output = suggest_outfit(listing, get_empty_wardrobe())

    assert isinstance(output, str)
    assert output.strip() != ""


def test_create_fit_card_empty_outfit(monkeypatch):
    monkeypatch.setattr("tools._call_groq", lambda prompt, temperature: "")
    listing = search_listings("vintage graphic tee", size="M", max_price=30)[0]

    output = create_fit_card("", listing)

    assert isinstance(output, str)
    assert output.strip() != ""
    assert "outfit" in output.lower()
    assert "empty" in output.lower() or "missing" in output.lower() or "invalid" in output.lower()


def test_interpret_query_fallback_basic(monkeypatch):
    monkeypatch.setattr("tools._call_groq", lambda prompt, temperature: "")

    result = interpret_query("I want a vintage graphic tee under 30 dollars")

    assert result == {
        "description": "vintage graphic tee",
        "size": None,
        "max_price": 30.0,
        "style": "vintage"
    }


def test_run_agent_uses_parsed_query_when_size_and_price_not_explicit(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        agent,
        "interpret_query",
        lambda user_query: {
            "description": "black hoodie",
            "size": "L",
            "max_price": 50.0,
            "style": None
        }
    )

    def fake_search(description, size, max_price):
        calls["search"] = (description, size, max_price)
        return [
            {
                "id": "T001",
                "title": "Black Hoodie",
                "description": "Test hoodie",
                "category": "hoodie",
                "style_tags": ["streetwear"],
                "size": "L",
                "condition": "good",
                "price": 40,
                "colors": ["black"],
                "brand": "Champion",
                "platform": "Depop"
            }
        ]

    monkeypatch.setattr(agent, "search_listings", fake_search)
    monkeypatch.setattr(agent, "suggest_outfit", lambda new_item, wardrobe: "outfit")
    monkeypatch.setattr(agent, "create_fit_card", lambda outfit, new_item: "fit card")

    session = agent.run_agent("Find me a black hoodie size L", wardrobe=get_empty_wardrobe())

    assert calls["search"] == ("black hoodie", "L", 50.0)
    assert session["parsed_query"]["description"] == "black hoodie"
    assert session["outfit_suggestion"] == "outfit"
    assert session["fit_card"] == "fit card"


def test_run_agent_prefers_explicit_size_and_price_over_parsed_values(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        agent,
        "interpret_query",
        lambda user_query: {
            "description": "black hoodie",
            "size": "L",
            "max_price": 50.0,
            "style": None
        }
    )

    def fake_search(description, size, max_price):
        calls["search"] = (description, size, max_price)
        return [
            {
                "id": "T002",
                "title": "Black Hoodie",
                "description": "Test hoodie",
                "category": "hoodie",
                "style_tags": ["streetwear"],
                "size": "M",
                "condition": "good",
                "price": 28,
                "colors": ["black"],
                "brand": "Gap",
                "platform": "Poshmark"
            }
        ]

    monkeypatch.setattr(agent, "search_listings", fake_search)
    monkeypatch.setattr(agent, "suggest_outfit", lambda new_item, wardrobe: "outfit")
    monkeypatch.setattr(agent, "create_fit_card", lambda outfit, new_item: "fit card")

    agent.run_agent(
        "Find me a black hoodie size L",
        size="M",
        max_price=30,
        wardrobe=get_empty_wardrobe()
    )

    assert calls["search"] == ("black hoodie", "M", 30)


def test_agent_stops_on_no_results(monkeypatch):
    calls = {"suggest_outfit": 0, "create_fit_card": 0}

    monkeypatch.setattr(
        agent,
        "interpret_query",
        lambda user_query: {
            "description": user_query,
            "size": None,
            "max_price": None,
            "style": None
        }
    )
    monkeypatch.setattr(agent, "search_listings", lambda description, size, max_price: [])

    def fake_suggest(new_item, wardrobe):
        calls["suggest_outfit"] += 1
        return "should not happen"

    def fake_card(outfit, new_item):
        calls["create_fit_card"] += 1
        return "should not happen"

    monkeypatch.setattr(agent, "suggest_outfit", fake_suggest)
    monkeypatch.setattr(agent, "create_fit_card", fake_card)

    session = run_agent("designer ballgown", size="XXS", max_price=5)

    assert session["error"] is not None
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None
    assert calls["suggest_outfit"] == 0
    assert calls["create_fit_card"] == 0
