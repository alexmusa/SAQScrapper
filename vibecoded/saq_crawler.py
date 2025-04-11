import os
import time
import random
import requests
from lxml import html
from urllib.parse import urlparse

BASE_URL = "https://www.saq.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}

def polite_sleep(min_delay=1.0, max_delay=2.5):
    """Sleep for a random time between requests to avoid hammering the server."""
    delay = random.uniform(min_delay, max_delay)
    print(f"Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)

def fetch_or_load_html(path, url=None):
    """Fetch from web if file does not exist, otherwise load from file."""
    if os.path.exists(path):
        print(f"Loading from {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    elif url:
        print(f"Fetching from {url}")
        polite_sleep()  # Respectful delay before request
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(response.text)
        return response.text
    else:
        raise FileNotFoundError(f"No URL provided and file not found: {path}")

def extract_slug(url):
    """Extract slug like 'vin' from a full SAQ category URL."""
    return urlparse(url).path.rstrip("/").split("/")[-1]

def parse_categories_recursively(url, save_dir="run", depth=0, max_depth=5):
    """Recursively parse a category page and return its structure with subcategories."""
    if depth > max_depth:
        return []

    slug = extract_slug(url)
    cat_dir = os.path.join(save_dir, slug)
    cat_file = os.path.join(cat_dir, f"{slug}.html")

    html_content = fetch_or_load_html(cat_file, url)
    tree = html.fromstring(html_content)
    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]/li')

    categories = []
    for item in items:
        name = item.xpath('.//a/text()[normalize-space()]')
        count = item.xpath('.//span[@class="count"]/text()')
        href = item.xpath('.//a/@href')

        if name and count and href:
            full_url = href[0].strip()
            clean_name = name[0].strip()
            clean_count = int(count[0].strip().replace('\xa0', '').replace(',', ''))
            sub_slug = extract_slug(full_url)

            # Recursively parse subcategories
            subcategories = parse_categories_recursively(full_url, save_dir, depth + 1, max_depth)

            categories.append({
                "name": clean_name,
                "slug": sub_slug,
                "url": full_url,
                "count": clean_count,
                "subcategories": subcategories
            })
    return categories

# Start with the main SAQ product page
main_url = f"{BASE_URL}/fr/produits"
main_slug = extract_slug(main_url)
main_file = f"./run/{main_slug}.html"
main_html = fetch_or_load_html(main_file, main_url)

# Parse top-level categories (with polite behavior)
category_tree = parse_categories_recursively(main_url)

# Output result
def print_tree(categories, indent=0):
    for cat in categories:
        print(" " * indent + f"- {cat['name']} ({cat['count']})")
        if cat['subcategories']:
            print_tree(cat['subcategories'], indent + 2)

print("\nSAQ Category Tree:")
print_tree(category_tree)
