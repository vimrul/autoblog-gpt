from app.db import db
from datetime import datetime

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    seo_title = db.Column(db.String(255))
    meta_description = db.Column(db.String(300))
    focus_keyword = db.Column(db.String(100))
    content = db.Column(db.Text)
    tags = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    image_webp = db.Column(db.String(255))
    wp_post_id = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
