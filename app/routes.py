from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Post
from app.db import db

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        topic = request.form.get("topic")
        model = request.form.get("model")

        if not topic:
            flash("Topic is required", "error")
            return redirect(url_for("main.home"))

        return redirect(url_for("main.preview", topic=topic, model=model))

    return render_template("home.html")
