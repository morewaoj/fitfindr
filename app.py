import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe


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


with gr.Blocks() as demo:
    gr.Markdown("# FitFindr: Multi-Tool AI Agent")
    gr.Markdown(
        "Search mock thrift listings, style the selected item with an example wardrobe, "
        "and generate a final fit card using a conditional multi-tool agent."
    )

    with gr.Row():
        query_input = gr.Textbox(label="Query", placeholder="vintage graphic tee")
        size_input = gr.Textbox(label="Size", placeholder="M")
        max_price_input = gr.Number(label="Max Price", value=30)

    find_button = gr.Button("Find Fit")

    selected_listing_output = gr.Textbox(
        label="Selected Listing",
        lines=8
    )
    outfit_output = gr.Textbox(
        label="Outfit Suggestion",
        lines=6
    )
    fit_card_output = gr.Textbox(
        label="Fit Card",
        lines=10
    )
    steps_output = gr.Textbox(
        label="Agent Steps / Error",
        lines=8
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
            ["jacket", None, 50],
            ["designer ballgown", "XXS", 5]
        ],
        inputs=[query_input, size_input, max_price_input]
    )


if __name__ == "__main__":
    demo.launch()
