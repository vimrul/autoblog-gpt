#!/bin/bash

# Project root
PROJECT="autoblog-gpt"
mkdir -p $PROJECT/app/templates $PROJECT/app/static
mkdir -p $PROJECT/storage/images $PROJECT/storage/articles

cd $PROJECT || exit

# Create core Python files
touch app/__init__.py app/routes.py app/db.py app/models.py
touch app/openai_handler.py app/wordpress_poster.py app/image_optimizer.py app/utils.py

# Templates
cat <<EOF > app/templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}AutoBlog GPT{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
EOF

touch app/templates/home.html
touch app/templates/preview.html
touch app/templates/settings.html
touch app/templates/post_history.html

# Styles
cat <<EOF > app/static/styles.css
body {
    font-family: Arial, sans-serif;
    padding: 2rem;
    background: #f7f7f7;
}
.container {
    max-width: 800px;
    margin: auto;
    background: white;
    padding: 2rem;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
EOF

# Dockerfile
cat <<EOF > Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080"]
EOF

# Docker Compose
cat <<EOF > docker-compose.yml
version: "3.9"

services:
  web:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    volumes:
      - ./storage:/app/storage
    depends_on:
      - db

  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: autoblog
      POSTGRES_USER: autobloguser
      POSTGRES_PASSWORD: securepass
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
EOF

# requirements.txt
cat <<EOF > requirements.txt
flask
requests
openai
psycopg2-binary
python-dotenv
Pillow
sqlalchemy
EOF

# .env (user must edit)
cat <<EOF > .env
FLASK_APP=app
FLASK_ENV=development

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4-1106-preview

# WordPress
WP_SITE_URL=https://your-wordpress-site.com
WP_USERNAME=your-username
WP_APP_PASSWORD=your-app-password

# PostgreSQL
DB_HOST=db
DB_PORT=5432
DB_NAME=autoblog
DB_USER=autobloguser
DB_PASSWORD=securepass
EOF

# README.md
cat <<EOF > README.md
# AutoBlog GPT

AutoBlog GPT is an AI-powered web application that generates SEO-friendly blog articles with ChatGPT, creates DALL·E featured images, and publishes them to WordPress automatically — with full Yoast SEO and tag support.

## Features
- GPT-4 article + SEO + image prompt
- DALL·E 3 image generation (converted to WebP)
- WordPress REST API posting (with featured image + Yoast + tags)
- PostgreSQL for history
- Accessible from anywhere (host on VPS)

## Getting Started

1. Edit the \`.env\` file with your API keys and WordPress credentials.
2. Run:
\`\`\`
docker-compose up --build
\`\`\`
3. Access at http://localhost:8080

## Storage
- Articles saved in: \`/storage/articles/\`
- Images saved in: \`/storage/images/\`

## License
MIT
EOF

echo "✅ Project 'autoblog-gpt' created. Edit .env and start with: docker-compose up --build"
