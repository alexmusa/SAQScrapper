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

def polite_sleep(min_delay=1.0, max_delay=20.0):
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
            print(f"Saving {url} under {path}")
            f.write(response.text)
        return response.text
    else:
        raise FileNotFoundError(f"No URL provided and file not found: {path}")

def extract_slug(url):
    """Extract slug like 'vin' from a full SAQ category URL."""
    return urlparse(url).path.rstrip("/").split("/")[-1]

def clean_url(href):
    if href: 
        return href[0].strip() 
    else: 
        return ''

def clean_name(name):
    if name:
        return name[0].strip()
    else:
        return ''

def clean_count(count):
    if count:
        return int(count[0].strip().replace('\xa0', '').replace(',', ''))
    else:
        return ''

def parse_parent(items):
    name = items.xpath('//li[contains(@class, "item-parent")]/a/text()[normalize-space()]')
    return clean_name(name)
    
def parse_current(items):
    name = items.xpath('//li[contains(@class, "item-current") and not(.//a)]/text()[normalize-space()]')
    count = items.xpath('//li[contains(@class, "item-current") and not(.//a)]/span[@class="count"]/text()')
    return clean_name(name), clean_count(count)

def parse_children_or_siblings(items):
    result = []
    for item in items.xpath('//li[contains(@class, "gtm-cat-filters-item")]'):
        name = item.xpath('.//a/text()[normalize-space()]')
        count = item.xpath('.//span[@class="count"]/text()')
        href = item.xpath('.//a/@href')
        result.append(
            (clean_name(name), clean_count(count), clean_url(href))
        )
    return result

def parse_categories_recursively(url, save_dir="run", depth=0, max_depth=5):
    """Recursively parse a category page and return its structure with subcategories."""
    categories = []
    if depth > max_depth:
        return categories

    slug = extract_slug(url)
    cat_dir = os.path.join(save_dir, slug)
    cat_file = os.path.join(cat_dir, f"{slug}.html")

    html_content = fetch_or_load_html(cat_file, url)
    tree = html.fromstring(html_content)
    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]')
    if not items:
        print(f"Leaf node reached.")
        return categories
    else:
        items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]')[0]

    # Unused. For debug purpose
    name = parse_parent(items)
    print(f"Parent: {name}")

    name, count = parse_current(items)
    print(f"Current: {name} ({count})")

    # If count is present, we have reached a leaf node
    if name and count:
        print(f"Leaf node reached.")
        return categories
    elif name and not count: # Subcategory
        print(f"Subcategory reached")
        pass
    elif not name and not count: # Main page
        print(f"Main page reached")
        pass
    else:
        raise Exception(f"Unexpected name and/or count for current category: {name} ({count})")

    for name, count, full_url in parse_children_or_siblings(items):
        #print(f"{name} ({count}) - {full_url}")
        #input("Press Enter to continue...")

        if name and count and full_url:
            sub_slug = extract_slug(full_url)

            # Recursively parse subcategories
            subcategories = parse_categories_recursively(full_url, cat_dir, depth + 1, max_depth)

            categories.append({
                "name": name,
                "slug": sub_slug,
                "url": full_url,
                "count": count,
                "subcategories": subcategories
            })
    return categories

# Start with the main SAQ product page
main_url = f"{BASE_URL}/fr/produits"
category_tree = parse_categories_recursively(main_url)

# Output result
def print_tree(categories, indent=0):
    for cat in categories:
        print(" " * indent + f"- {cat['name']} ({cat['count']})")
        if cat['subcategories']:
            print_tree(cat['subcategories'], indent + 2)

print("\nSAQ Category Tree:")
print_tree(category_tree)
