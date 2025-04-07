import os
import uuid
import json
import glob
import markdown
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.openai_handler import generate_article
from app.wordpress_poster import fetch_categories, post_article_to_wp
from app.models import Post, ScheduledPost
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

    # Ensure the directory exists
    os.makedirs("storage/articles", exist_ok=True)
    file_path = f"storage/articles/{preview_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

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

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["category_ids"] = category_ids

    wp_post_id = post_article_to_wp(data)
    if not wp_post_id:
        flash("Failed to post to WordPress", "error")
        return redirect(url_for("main.preview", topic=data['topic'], model=data['model'], categories=",".join(map(str, category_ids))))

    post = Post(
        topic=data["topic"],
        seo_title=data["seo_title"],
        meta_description=data["meta_description"],
        focus_keyword=data["focus_keyword"],
        content=data["article"] if "article" in data else data.get("main_article_body", ""),
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
    files = glob.glob("storage/articles/*.json")
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data.get("topic") == topic:
                html = markdown.markdown(data.get("article", ""))
                return render_template("preview.html", data=data, rendered_article=html)

    flash("Article not found.", "error")
    return redirect(url_for("main.post_history"))


@main.route("/settings", methods=["GET", "POST"])
def settings():
    settings_path = "config/settings.json"
    settings = {}

    # Load current settings
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

    if request.method == "POST":
        updated_keys = ["OPENAI_API_KEY", "OPENAI_MODEL", "WP_SITE_URL", "WP_USERNAME", "WP_APP_PASSWORD"]
        for key in updated_keys:
            settings[key] = request.form.get(key, "")

        os.makedirs("config", exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

        flash("✅ Settings updated successfully!", "success")
        return redirect(url_for("main.settings"))

    return render_template("settings.html", settings=settings)



@main.route("/schedule", methods=["GET", "POST"])
def schedule_post():
    categories = fetch_categories()

    if request.method == "POST":
        topic = request.form.get("topic")
        model = request.form.get("model", "gpt-4-1106-preview")
        category_ids = request.form.getlist("categories")
        scheduled_time = request.form.get("scheduled_time")

        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_time)
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("main.schedule_post"))

        result = generate_article(topic, model)
        if not result:
            flash("Failed to generate article", "error")
            return redirect(url_for("main.schedule_post"))

        post = ScheduledPost(
            topic=topic,
            seo_title=result["seo_title"],
            meta_description=result["meta_description"],
            focus_keyword=result["focus_keyword"],
            content=result["article"],
            tags=result["tags"],
            image_prompt=result["image_prompt"],
            category_ids=",".join(category_ids),
            scheduled_time=scheduled_datetime
        )
        db.session.add(post)
        db.session.commit()

        flash("✅ Post scheduled successfully!", "success")
        return redirect(url_for("main.post_history"))

    return render_template("schedule.html", categories=categories)
