import openai
import os
import json
import sys
import re

def load_settings():
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def generate_article(topic, model=None):
    settings = load_settings()
    openai.api_key = settings.get("OPENAI_API_KEY")
    model = model or settings.get("OPENAI_MODEL", "gpt-4")

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

Respond ONLY in raw JSON format (no markdown or code block).
"""

    try:
        print("[INFO] Generating article using:", model, file=sys.stderr)

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful content assistant."},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.7
        )

        raw = response.choices[0].message['content']
        print("[DEBUG] Raw GPT content:\n", raw, file=sys.stderr)

        raw = raw.strip().lstrip("`json").strip("`").strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        json_str = raw[start:end]

        match = re.search(r'"article"\s*:\s*"(.*?)"\s*}', json_str, re.DOTALL)
        if match:
            article_raw = match.group(1)
            article_escaped = (
                article_raw.replace('\\', '\\\\')
                           .replace('"', '\\"')
                           .replace('\n', '\\n')
            )
            json_str = re.sub(
                r'"article"\s*:\s*"(.*?)"\s*}',
                f'"article": "{article_escaped}"}}',
                json_str,
                flags=re.DOTALL
            )

        result = json.loads(json_str)

        if "article_body" in result:
            result["article"] = result.pop("article_body")

        return result

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode failed: {e}\nContent:\n{json_str}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERROR] GPT generation failed: {e}", file=sys.stderr)
        return None
