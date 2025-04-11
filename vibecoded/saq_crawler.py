import os
import requests
from lxml import html
from urllib.parse import urlparse

BASE_URL = "https://www.saq.com"

def fetch_or_load_html(path, url=None):
    """Fetch from web if file does not exist, otherwise load from file."""
    if os.path.exists(path):
        print(f"Loading from {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    elif url:
        print(f"Fetching from {url}")
        response = requests.get(url)
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

def extract_categories(html_content):
    """Extract categories/subcategories (name, count, URL, slug) from an SAQ page."""
    tree = html.fromstring(html_content)
    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]/li')
    
    categories = []
    for item in items:
        name = item.xpath('.//a/text()[normalize-space()]')
        count = item.xpath('.//span[@class="count"]/text()')
        url = item.xpath('.//a/@href')
        if name and count and url:
            clean_name = name[0].strip()
            clean_count = int(count[0].strip().replace('\xa0', '').replace(',', ''))
            full_url = url[0].strip()
            categories.append({
                "name": clean_name,
                "count": clean_count,
                "url": full_url,
                "slug": extract_slug(full_url)
            })
    return categories

# Step 1: Load or fetch main product page
main_path = "./run/produits.html"
main_url = f"{BASE_URL}/fr/produits"
main_html = fetch_or_load_html(main_path, main_url)

# Step 2: Extract main product categories
categories = extract_categories(main_html)

# BEGIN_MINE: Check if it function correctly
# for cat in categories:
#     print(f"\nCategory: {cat['name']} - {cat['slug']} ({cat['count']} articles) {cat['url']}")
# END_MINE  

# Step 3: For each category, fetch its page and extract subcategories
for cat in categories:
    cat_dir = os.path.join("run", cat["slug"])
    cat_file = os.path.join(cat_dir, f"{cat['slug']}.html")
    cat_html = fetch_or_load_html(cat_file, cat["url"])
    subcategories = extract_categories(cat_html)

    # Output category and its subcategories
    print(f"\nCategory: {cat['name']} ({cat['count']} articles)")
    for sub in subcategories:
        print(f"  ↳ Subcategory: {sub['name']} - {sub['slug']} ({sub['count']} articles)\n{sub['url']}")

