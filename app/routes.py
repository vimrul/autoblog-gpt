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
