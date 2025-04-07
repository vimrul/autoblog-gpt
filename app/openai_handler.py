import openai
import os
import json
import sys
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_article(topic, model="gpt-4"):
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

Respond ONLY in valid raw JSON. Do not include markdown, triple backticks, or code fencing.
"""

    try:
        print(f"[INFO] Generating article using: {model}", file=sys.stderr)

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

        # Clean up markdown/code block artifacts
        raw = raw.strip().lstrip("`json").strip("`").strip()

        # Extract JSON block
        start, end = raw.find("{"), raw.rfind("}") + 1
        json_str = raw[start:end]

        parsed = json.loads(json_str)

        # Normalize keys
        if "article_body" in parsed:
            parsed["article"] = parsed.pop("article_body")
        elif "Main_Article_Body" in parsed:
            parsed["article"] = parsed.pop("Main_Article_Body")

        return parsed

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode failed: {e}\nContent:\n{raw}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERROR] GPT generation failed: {e}", file=sys.stderr)
        return None
