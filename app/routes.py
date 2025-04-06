import os
import uuid
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.openai_handler import generate_article
from app.wordpress_poster import fetch_categories, post_article_to_wp
from app.models import Post
from app.db import db

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def home():
    categories = fetch_categories()

    if request.method == "POST":
        topic = request.form.get("topic")
        model = request.form.get("model", "gpt-4-1106-preview")
        selected_categories = request.form.getlist("categories") or []

        if not topic:
            flash("Topic is required", "error")
            return redirect(url_for("main.home"))

        return redirect(
            url_for("main.preview", topic=topic, model=model, categories=",".join(selected_categories))
        )

    return render_template("home.html", categories=categories)


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


@main.route("/post_to_wp", methods=["POST"])
def post_to_wp():
    preview_id = request.form.get("preview_id")
    category_ids = request.form.get("category_ids", "")
    category_ids = [int(cid) for cid in category_ids.split(",") if cid.strip().isdigit()]

    file_path = f"storage/articles/{preview_id}.json"
    if not os.path.exists(file_path):
        flash("Preview data not found", "error")
        return redirect(url_for("main.home"))

    with open(file_path, "r") as f:
        data = json.load(f)

    # Attach categories to data
    data["category_ids"] = category_ids

    # Post to WP
    wp_post_id = post_article_to_wp(data)
    if not wp_post_id:
        flash("Failed to post to WordPress", "error")
        return redirect(url_for("main.preview", topic=data['topic'], model=data['model'], categories=",".join(map(str, category_ids))))

    # Save to DB
    post = Post(
        topic=data["topic"],
        seo_title=data["seo_title"],
        meta_description=data["meta_description"],
        focus_keyword=data["focus_keyword"],
        content=data["article"],
        tags=data["tags"],
        image_path=data.get("image_path", ""),
        image_webp=data.get("image_webp", ""),
        wp_post_id=str(wp_post_id)
    )
    db.session.add(post)
    db.session.commit()

    flash(f"✅ Successfully posted to WordPress (Post ID: {wp_post_id})", "success")
    return redirect(url_for("main.home"))

@main.route("/history")
def post_history():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("post_history.html", posts=posts)

@main.route("/view_article/<topic>")
def view_article(topic):
    import glob
    import markdown

    files = glob.glob(f"storage/articles/*.json")
    for f in files:
        with open(f, "r") as file:
            import json
            data = json.load(file)
            if data.get("topic") == topic:
                html = markdown.markdown(data["article"])
                return render_template("preview.html", data=data, rendered_article=html)
    flash("Article not found.", "error")
    return redirect(url_for("main.post_history"))
