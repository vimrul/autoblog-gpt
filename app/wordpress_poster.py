import requests
import os
from requests.auth import HTTPBasicAuth

def fetch_categories():
    wp_url = os.getenv("WP_SITE_URL")
    user = os.getenv("WP_USERNAME")
    password = os.getenv("WP_APP_PASSWORD")

    try:
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/categories?per_page=100",
            auth=HTTPBasicAuth(user, password)
        )
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch categories:", response.text)
            return []
    except Exception as e:
        print(f"[ERROR] Category fetch failed: {e}")
        return []
