import os
import io
import base64
import time
import openai
import requests
from PIL import Image
from requests.auth import HTTPBasicAuth
from app.utils.settings import get_settings

# Load settings from settings.json
settings = get_settings()
WP_URL = settings.get("WP_SITE_URL")
WP_USER = settings.get("WP_USERNAME")
WP_PASS = settings.get("WP_APP_PASSWORD")
AUTH = HTTPBasicAuth(WP_USER, WP_PASS)


# ======================
# Fetch Available Categories
# ======================
def fetch_categories():
    try:
        response = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=100", auth=AUTH)
        if response.status_code == 200:
            return response.json()
        print("[ERROR] Fetching categories:", response.text)
    except Exception as e:
        print(f"[ERROR] Category fetch failed: {e}")
    return []


# ====================
# Resolve Tags to IDs
# ====================
def resolve_tags(tag_names):
    tag_ids = []

    for tag in tag_names:
        tag = tag.strip()
        if not tag:
            continue
        try:
            check = requests.get(f"{WP_URL}/wp-json/wp/v2/tags?search={tag}", auth=AUTH)
            if check.status_code == 200 and check.json():
                tag_ids.append(check.json()[0]['id'])
            else:
                create = requests.post(
                    f"{WP_URL}/wp-json/wp/v2/tags",
                    json={"name": tag},
                    auth=AUTH
                )
                if create.status_code in [200, 201]:
                    tag_ids.append(create.json()['id'])
        except Exception as e:
            print(f"[ERROR] Tag resolution failed for '{tag}': {e}")

    return tag_ids


# ===========================
# Generate + Upload Image
# ===========================
def generate_and_upload_image(prompt, preview_id):
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

    image_path = f"storage/images/{preview_id}.png"
    image_webp = f"storage/images/{preview_id}.webp"
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    # Save PNG
    image_bytes = io.BytesIO(base64.b64decode(image_data))
    with open(image_path, "wb") as f:
        f.write(image_bytes.getbuffer())

    # Convert to WebP
    try:
        with Image.open(image_path) as img:
            img.save(image_webp, "webp")
    except Exception as e:
        print(f"[ERROR] WebP conversion failed: {e}")
        image_webp = None

    # Upload PNG to WordPress
    try:
        headers = {
            "Content-Disposition": f"attachment; filename={preview_id}.png",
            "Content-Type": "image/png"
        }
        with open(image_path, "rb") as img_file:
            media_response = requests.post(
                f"{WP_URL}/wp-json/wp/v2/media",
                headers=headers,
                data=img_file,
                auth=AUTH
            )
        if media_response.status_code in [200, 201]:
            media_id = media_response.json()["id"]
            return media_id, image_webp
        else:
            print(f"[ERROR] Uploading image to WordPress: {media_response.text}")
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")

    return None, image_webp


# ======================
# Format Article Body
# ======================
def format_article_body(data):
    body = data.get("main_article_body")
    if isinstance(body, dict):
        html = ""

        if "introduction" in body:
            intro = body["introduction"]
            if isinstance(intro, dict):
                html += f"<p>{intro.get('hook', '')}</p><p>{intro.get('overview', '')}</p>"
            else:
                html += f"<p>{intro}</p>"

        if "sections" in body and isinstance(body["sections"], list):
            for section in body["sections"]:
                html += f"<h2>{section.get('title')}</h2><p>{section.get('content')}</p>"

        for k, v in body.items():
            if isinstance(v, dict) and "header" in v and "content" in v:
                html += f"<h2>{v['header']}</h2><p>{v['content']}</p>"
            elif isinstance(v, dict) and "sub_heading" in v and "content" in v:
                html += f"<h3>{v['sub_heading']}</h3><p>{v['content']}</p>"

        if "conclusion" in body:
            concl = body["conclusion"]
            if isinstance(concl, dict):
                html += f"<h2>{concl.get('header', 'Conclusion')}</h2><p>{concl.get('content', '')}</p>"
            elif isinstance(concl, str):
                html += f"<h2>Conclusion</h2><p>{concl}</p>"

        return html or str(body)

    return body or ""


# ===============================
# Main Post Creation to WordPress
# ===============================
def post_article_to_wp(data):
    title = data.get("title") or data.get("catchy_title") or "Untitled"
    content = data.get("article") or format_article_body(data)
    seo_title = data.get("seo_title") or ""
    meta_description = data.get("meta_description") or ""
    focus_keyword = data.get("focus_keyword") or ""
    tags = data.get("tags", "")
    category_ids = data.get("category_ids", [])
    image_prompt = data.get("image_prompt") or data.get("suggested_image_prompt") or ""
    preview_id = data.get("preview_id")

    print(f"[INFO] Posting article: {title}")
    print(f"[INFO] Categories: {category_ids}, Tags: {tags}")

    media_id, image_webp_path = generate_and_upload_image(image_prompt, preview_id)
    if not media_id:
        print("[WARN] Failed to attach featured image")

    tag_names = [tag.strip() for tag in tags.split(",") if tag.strip()]
    tag_ids = resolve_tags(tag_names)

    post_payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": category_ids,
        "tags": tag_ids,
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
        print(f"[SUCCESS] Article posted with ID: {post_id}")

        # Attach SEO meta
        meta_fields = {
            "yoast_title": seo_title,
            "yoast_metadesc": meta_description,
            "focus_keyword": focus_keyword
        }

        for key, value in meta_fields.items():
            try:
                meta_response = requests.post(
                    f"{WP_URL}/wp-json/wp/v2/posts/{post_id}/meta",
                    auth=AUTH,
                    json={"key": key, "value": value}
                )
                time.sleep(0.2)
            except Exception as e:
                print(f"[ERROR] Setting meta '{key}': {e}")

        data["image_path"] = f"storage/images/{preview_id}.png"
        data["image_webp"] = image_webp_path

        return post_id

    except Exception as e:
        print(f"[ERROR] WordPress post failed: {e}")
        return None
