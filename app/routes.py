from app.wordpress_poster import fetch_categories

@main.route("/", methods=["GET", "POST"])
def home():
    categories = fetch_categories()

    if request.method == "POST":
        topic = request.form.get("topic")
        model = request.form.get("model")
        selected_categories = request.form.getlist("categories")

        if not topic:
            flash("Topic is required", "error")
            return redirect(url_for("main.home"))

        return redirect(
            url_for("main.preview", topic=topic, model=model, categories=",".join(selected_categories))
        )

    return render_template("home.html", categories=categories)

import json

@main.route("/preview")
def preview():
    topic = request.args.get("topic")
    model = request.args.get("model", "gpt-4-1106-preview")
    category_ids = request.args.get("categories", "")  # comma-separated

    result = generate_article(topic, model)
    if not result:
        flash("Article generation failed.", "error")
        return redirect(url_for("main.home"))

    # Store everything for later
    preview_id = str(uuid.uuid4())
    session_data = {
        "preview_id": preview_id,
        "topic": topic,
        "model": model,
        "category_ids": category_ids,
        **result
    }

    with open(f"storage/articles/{preview_id}.json", "w") as f:
        json.dump(session_data, f)

    return render_template("preview.html", data=session_data)