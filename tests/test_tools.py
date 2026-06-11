from agent import run_agent
from tools import create_fit_card, search_listings, suggest_outfit
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


def test_agent_stops_on_no_results():
    session = run_agent("designer ballgown", size="XXS", max_price=5)

    assert session["error"] is not None
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None
