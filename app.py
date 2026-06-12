import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe


APP_CSS = """
:root {
    --fit-green: #16a34a;
    --fit-green-dark: #0f7a38;
    --fit-mint: #dcfce7;
    --fit-lime: #bbf7d0;
    --fit-text: #102118;
    --fit-muted: #52645a;
    --fit-border: #b7e4c7;
}

body,
.gradio-container {
    background:
        radial-gradient(circle at 12% 8%, rgba(187, 247, 208, 0.9), transparent 28%),
        radial-gradient(circle at 88% 16%, rgba(34, 197, 94, 0.18), transparent 30%),
        linear-gradient(180deg, #f7fff9 0%, #ffffff 45%, #effdf4 100%) !important;
    color: var(--fit-text) !important;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.gradio-container {
    max-width: 1120px !important;
    margin: 0 auto !important;
    padding: 28px !important;
}

.fit-hero {
    background: linear-gradient(135deg, #16a34a 0%, #22c55e 52%, #86efac 100%);
    border: 1px solid rgba(255, 255, 255, 0.55);
    border-radius: 24px;
    box-shadow: 0 24px 80px rgba(22, 163, 74, 0.24);
    color: white;
    padding: 34px;
    margin-bottom: 22px;
}

.fit-hero h1 {
    font-size: clamp(2rem, 5vw, 4rem);
    line-height: 1;
    margin: 0 0 12px 0;
    letter-spacing: 0;
}

.fit-hero p {
    font-size: 1.08rem;
    line-height: 1.65;
    max-width: 760px;
    margin: 0;
}

.fit-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 20px;
}

.fit-chip {
    background: rgba(255, 255, 255, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.38);
    border-radius: 999px;
    color: white;
    font-size: 0.9rem;
    font-weight: 700;
    padding: 8px 13px;
}

.input-panel,
.output-panel {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid var(--fit-border);
    border-radius: 22px;
    box-shadow: 0 16px 42px rgba(15, 122, 56, 0.12);
    padding: 18px;
}

.gradio-container label {
    color: var(--fit-green-dark) !important;
    font-size: 0.78rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

textarea,
input {
    border-color: var(--fit-border) !important;
    border-radius: 16px !important;
}

textarea:focus,
input:focus {
    border-color: var(--fit-green) !important;
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.16) !important;
}

.find-button button,
button.primary {
    background: linear-gradient(135deg, #15803d, #22c55e) !important;
    border: none !important;
    border-radius: 999px !important;
    box-shadow: 0 12px 28px rgba(22, 163, 74, 0.28) !important;
    color: white !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    min-height: 48px !important;
}

.find-button button:hover,
button.primary:hover {
    filter: brightness(1.05);
    transform: translateY(-1px);
}

.output-panel textarea {
    background: #fbfffc !important;
    color: var(--fit-text) !important;
    line-height: 1.55 !important;
}

.steps-box textarea {
    background: #f0fdf4 !important;
}
"""


def format_listing(item):
    if not isinstance(item, dict) or not item:
        return "No listing selected."

    title = item.get("title", "Unknown title")
    price = item.get("price", "Unknown price")
    size = item.get("size", "Unknown size")
    condition = item.get("condition", "Unknown condition")
    platform = item.get("platform", "Unknown platform")
    colors = item.get("colors", [])
    brand = item.get("brand", "Unknown brand")

    if isinstance(price, int) or isinstance(price, float):
        price_text = f"${price:.2f}"
    else:
        price_text = str(price)

    if isinstance(colors, list):
        colors_text = ", ".join(str(color) for color in colors)
    else:
        colors_text = str(colors)

    return (
        f"Title: {title}\n"
        f"Price: {price_text}\n"
        f"Size: {size}\n"
        f"Condition: {condition}\n"
        f"Platform: {platform}\n"
        f"Colors: {colors_text}\n"
        f"Brand: {brand}"
    )


def format_steps(steps, error=None):
    lines = []

    if error:
        lines.append(f"Error: {error}")
        lines.append("")

    if steps:
        for index, step in enumerate(steps, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("No steps recorded.")

    return "\n".join(lines)


def handle_query(query, size, max_price):
    if not isinstance(query, str) or not query.strip():
        return (
            "No listing selected.",
            "Not generated because the query was empty.",
            "Not generated because the workflow stopped early.",
            "Error: Please enter a thrift item to search for."
        )

    clean_query = query.strip()
    clean_size = None

    if isinstance(size, str) and size.strip():
        clean_size = size.strip()

    clean_max_price = None

    if max_price is not None:
        clean_max_price = float(max_price)

    wardrobe = get_example_wardrobe()
    session = run_agent(
        clean_query,
        size=clean_size,
        max_price=clean_max_price,
        wardrobe=wardrobe
    )

    if session["error"]:
        return (
            "No listing selected.",
            "Not generated because search did not return a usable item.",
            "Not generated because the workflow stopped early.",
            format_steps(session["steps"], session["error"])
        )

    return (
        format_listing(session["selected_item"]),
        session["outfit_suggestion"],
        session["fit_card"],
        format_steps(session["steps"])
    )


with gr.Blocks(title="FitFindr") as demo:
    gr.HTML(
        """
        <section class="fit-hero">
            <h1>FitFindr</h1>
            <p>
                Find thrift gems, style them with your closet, and turn the whole thing
                into a fresh fit card. Search smart, stop early when nothing matches,
                and let the agent do the outfit math.
            </p>
            <div class="fit-chip-row">
                <span class="fit-chip">Live thrift search</span>
                <span class="fit-chip">Wardrobe-aware styling</span>
                <span class="fit-chip">Fit card generator</span>
            </div>
        </section>
        """
    )

    with gr.Group(elem_classes=["input-panel"]):
        with gr.Row():
            query_input = gr.Textbox(
                label="What are you hunting for?",
                placeholder="vintage graphic tee",
                lines=2
            )
            size_input = gr.Textbox(label="Size", placeholder="M")
            max_price_input = gr.Number(label="Max Price", value=None)

        find_button = gr.Button("Find Fit", variant="primary", elem_classes=["find-button"])

    with gr.Group(elem_classes=["output-panel"]):
        with gr.Row():
            selected_listing_output = gr.Textbox(
                label="Selected Listing",
                lines=8
            )
            outfit_output = gr.Textbox(
                label="Outfit Suggestion",
                lines=8
            )
        fit_card_output = gr.Textbox(
            label="Fit Card",
            lines=10
        )
        steps_output = gr.Textbox(
            label="Agent Steps / Error",
            lines=8,
            elem_classes=["steps-box"]
        )

    find_button.click(
        fn=handle_query,
        inputs=[query_input, size_input, max_price_input],
        outputs=[
            selected_listing_output,
            outfit_output,
            fit_card_output,
            steps_output
        ]
    )

    gr.Examples(
        examples=[
            ["vintage graphic tee", "M", 30],
            ["black hoodie", "", 50],
            ["baggy jeans", "", 100],
            ["white sneakers", "", 120],
            ["workwear boots", "", 150],
            ["designer ballgown", "XXS", 5]
        ],
        inputs=[query_input, size_input, max_price_input]
    )


if __name__ == "__main__":
    demo.launch(css=APP_CSS)
