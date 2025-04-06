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
