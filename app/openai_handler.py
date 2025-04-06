import openai
import os
import json

# Set API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_article(topic, model="gpt-4-1106-preview"):
    prompt = f"""
You are a professional blog writer. Write a long-form SEO-optimized blog article on the topic:
"{topic}"

Include:
- Catchy title
- SEO title (max 60 chars)
- Meta description (max 160 chars)
- Focus keyword
- Social title (same as title)
- Social description (same as meta description)
- Tags (comma-separated, 3–6)
- Suggested image prompt for DALL·E (landscape, high quality)
- Main article body (scannable, human-like)

Respond in JSON format like:
{{
"title": "...",
"seo_title": "...",
"meta_description": "...",
"focus_keyword": "...",
"social_title": "...",
"social_description": "...",
"tags": "...",
"image_prompt": "...",
"article": "..."
}}
"""

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful content assistant."},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.7
        )

        content = response.choices[0].message['content']
        print("[DEBUG] Raw GPT content:\n", content)  # ✅ Helpful for testing

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode failed: {e}")
            return None

    except Exception as e:
        print(f"[ERROR] GPT generation failed: {e}")
        return None
