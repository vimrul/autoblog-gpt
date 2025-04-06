import os
import requests
from requests.auth import HTTPBasicAuth
from PIL import Image
import openai
import io
import time

# Load credentials
WP_URL = os.getenv("WP_SITE_URL")
WP_USER = os.getenv("WP_USERNAME")
WP_PASS = os.getenv("WP_APP_PASSWORD")
AUTH = HTTPBasicAuth(WP_USER, WP_PASS)

# --- STEP 1: Upload Image to WordPress ---
def generate_and_upload_image(prompt, preview_id):
    # Generate image from OpenAI
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            response_format="b64_json"
        )
        image_data = response['data'][0]['b64_json']
    except Exception as e:
        print(f"[ERROR] DALL·E image generation failed: {e}")
        return None, None

    # Save PNG
    image_bytes = io.BytesIO(base64.b64decode(image_data))
    image_path = f"storage/images/{preview_id}.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes.getbuffer())

    # Convert to WebP
    image_webp = f"storage/images/{preview_id}.webp"
    with Image.open(image_path) as img:
        img.save(image_webp, "webp")

    # Upload PNG to WordPress
    try:
        headers = {
            "Content-Disposition": f"attachment; filename={preview_id}.png",
            "Content-Type": "image/png"
        }
        media_response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers=headers,
            data=open(image_path, "rb"),
            auth=AUTH
        )
        if media_response.status_code in [200, 201]:
            media_id = media_response.json()["id"]
            return media_id, image_webp
        else:
            print(f"[ERROR] Uploading image to WordPress: {media_response.text}")
            return None, image_webp
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return None, image_webp
def post_article_to_wp(data):
    title = data["title"]
    content = data["article"]
    seo_title = data["seo_title"]
    meta_description = data["meta_description"]
    focus_keyword = data["focus_keyword"]
    tags = data["tags"]
    category_ids = data.get("category_ids", [])
    image_prompt = data.get("image_prompt", "")
    preview_id = data.get("preview_id")

    media_id, image_webp_path = generate_and_upload_image(image_prompt, preview_id)
    if not media_id:
        print("[WARN] Failed to attach featured image")

    # Create the post
    post_payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": category_ids,
        "tags": [t.strip() for t in tags.split(",")],
        "featured_media": media_id
    }

    try:
        post_res = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            json=post_payload,
            auth=AUTH
        )
        if post_res.status_code not in [200, 201]:
            print(f"[ERROR] Failed to post article: {post_res.text}")
            return None

        post_id = post_res.json()["id"]

        # Set Yoast meta fields
        meta_fields = {
            "yoast_head_json": {
                "title": seo_title,
                "description": meta_description
            },
            "meta_description": meta_description,
            "focus_keyword": focus_keyword
        }

        for key, value in meta_fields.items():
            meta_response = requests.post(
                f"{WP_URL}/wp-json/wp/v2/posts/{post_id}/meta",
                auth=AUTH,
                json={"key": key, "value": value}
            )
            time.sleep(0.2)  # Avoid rate limit

        # Add image path info
        data["image_path"] = f"storage/images/{preview_id}.png"
        data["image_webp"] = image_webp_path

        return post_id

    except Exception as e:
        print(f"[ERROR] WordPress post failed: {e}")
        return None
