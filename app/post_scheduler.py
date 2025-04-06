from app import create_app
from app.db import db
from app.models import ScheduledPost
from app.wordpress_poster import post_article_to_wp
from datetime import datetime

app = create_app()

with app.app_context():
    now = datetime.utcnow()
    queue = ScheduledPost.query.filter(
        ScheduledPost.scheduled_time <= now,
        ScheduledPost.posted == False
    ).all()

    for post in queue:
        print(f"⏳ Posting: {post.topic}")
        post_data = {
            "title": post.seo_title,
            "article": post.content,
            "seo_title": post.seo_title,
            "meta_description": post.meta_description,
            "focus_keyword": post.focus_keyword,
            "tags": post.tags,
            "image_prompt": post.image_prompt,
            "category_ids": [int(cid) for cid in post.category_ids.split(",")],
            "preview_id": f"scheduled-{post.id}"
        }

        wp_id = post_article_to_wp(post_data)
        if wp_id:
            post.posted = True
            post.wp_post_id = wp_id
            db.session.commit()
            print(f"✅ Posted: {post.topic}")
        else:
            print(f"❌ Failed to post: {post.topic}")
