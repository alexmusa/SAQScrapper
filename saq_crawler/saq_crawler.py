import os
import time
import random
import json
import requests
from lxml import html
from urllib.parse import urlparse

BASE_URL = "https://www.saq.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def polite_sleep(min_delay=1.0, max_delay=10.0):
    """Random delay to avoid overloading the server."""
    delay = random.uniform(min_delay, max_delay)
    print(f"Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)


def fetch_or_load_html(filepath, url=None):
    """Load HTML from local file or fetch from URL and save locally."""
    if os.path.exists(filepath):
        print(f"Loading from {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    if not url:
        raise FileNotFoundError(f"No URL provided and file not found: {filepath}")

    print(f"Fetching from {url}")
    polite_sleep()
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        print(f"Saving content to {filepath}")
        f.write(response.text)

    return response.text


def extract_slug(url):
    return urlparse(url).path.rstrip("/").split("/")[-1]


def clean_text(element):
    return element[0].strip() if element else ''


def clean_count_text(count):
    return int(count[0].strip().replace('\xa0', '').replace(',', '')) if count else ''


def parse_breadcrumbs(items):
    """Extract category breadcrumb navigation."""
    parent_name = clean_text(items.xpath('//li[contains(@class, "item-parent")]/a/text()[normalize-space()]'))
    current_name = clean_text(
        items.xpath('//li[contains(@class, "item-current") and not(.//a)]/text()[normalize-space()]')
    )
    current_count = clean_count_text(
        items.xpath('//li[contains(@class, "item-current") and not(.//a)]/span[@class="count"]/text()')
    )
    return parent_name, current_name, current_count


def parse_subcategories(items):
    """Extract subcategory information (name, count, URL)."""
    subcategories = []
    for item in items.xpath('//li[contains(@class, "gtm-cat-filters-item")]'):
        name = clean_text(item.xpath('.//a/text()[normalize-space()]'))
        count = clean_count_text(item.xpath('.//span[@class="count"]/text()'))
        href = clean_text(item.xpath('.//a/@href'))
        if name and count and href:
            subcategories.append((name, count, href))
    return subcategories


def parse_categories_recursively(url, save_dir="run", depth=0, max_depth=5):
    """Recursive category parser that builds a category tree."""
    if depth > max_depth:
        return []

    slug = extract_slug(url)
    dir_path = os.path.join(save_dir, slug)
    file_path = os.path.join(dir_path, f"{slug}.html")
    html_content = fetch_or_load_html(file_path, url)
    tree = html.fromstring(html_content)

    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]')
    if not items:
        print("Leaf node reached (no items found).")
        return []

    items = items[0]
    parent_name, current_name, current_count = parse_breadcrumbs(items)
    print(f"Parent: {parent_name}")
    print(f"Current: {current_name} ({current_count})")

    if current_name and current_count:
        print("Leaf node reached.")
        return []

    print("Subcategory" if current_name else "Main category")

    categories = []
    for name, count, href in parse_subcategories(items):
        print(f"Parsing subcategory: {name} ({count})")
        sub_slug = extract_slug(href)
        sub_tree = parse_categories_recursively(href, dir_path, depth + 1, max_depth)
        categories.append({
            "name": name,
            "slug": sub_slug,
            "url": href,
            "count": count,
            "subcategories": sub_tree
        })
    return categories


def print_category_tree(categories, indent=0):
    for cat in categories:
        print(" " * indent + f"- {cat['name']} ({cat['count']})")
        if cat['subcategories']:
            print_category_tree(cat['subcategories'], indent + 2)


if __name__ == "__main__":
    main_url = f"{BASE_URL}/fr/produits"
    tree = parse_categories_recursively(main_url)

    # Save category tree to JSON
    save_dir="run"
    output_file = os.path.join(save_dir, "category_tree.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"\nCategory tree saved to {output_file}")

    # Optionally print the tree
    print("\nSAQ Category Tree:")
    print_category_tree(tree)
