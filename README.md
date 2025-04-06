# AutoBlog GPT

AutoBlog GPT is an AI-powered web application that generates SEO-friendly blog articles with ChatGPT, creates DALL·E featured images, and publishes them to WordPress automatically — with full Yoast SEO and tag support.

## Features
- GPT-4 article + SEO + image prompt
- DALL·E 3 image generation (converted to WebP)
- WordPress REST API posting (with featured image + Yoast + tags)
- PostgreSQL for history
- Accessible from anywhere (host on VPS)

## Getting Started

1. Edit the `.env` file with your API keys and WordPress credentials.
2. Run:
```
docker-compose up --build
```
3. Access at http://localhost:8080

## Storage
- Articles saved in: `/storage/articles/`
- Images saved in: `/storage/images/`

## License
MIT
