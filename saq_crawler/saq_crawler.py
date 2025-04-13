import os
import time
import random
import json
import logging
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


def setup_logging(save_dir="run"):
    """Configure logging to output to console and a log file."""
    os.makedirs(save_dir, exist_ok=True)
    log_file = os.path.join(save_dir, "saq_crawler.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging is set up.")


def polite_sleep(min_delay=1.0, max_delay=10.0):
    """Random delay to avoid overloading the server."""
    delay = random.uniform(min_delay, max_delay)
    logging.info(f"Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)


def fetch_or_load_html(filepath, url=None):
    """Load HTML from local file or fetch from URL and save locally."""
    if os.path.exists(filepath):
        logging.info(f"Loading from {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    if not url:
        raise FileNotFoundError(f"No URL provided and file not found: {filepath}")

    logging.info(f"Fetching from {url}")
    polite_sleep()
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        logging.info(f"Saving content to {filepath}")
        f.write(response.text)

    return response.text

def save_all_category_pages(base_url, save_dir="run", product_list_limit=96):
    """Fetch and save all pages of a category listing based on pagination."""
    from math import ceil

    slug = extract_slug(base_url)
    dir_path = os.path.join(save_dir, slug)
    os.makedirs(dir_path, exist_ok=True)

    def page_file_path(page_num):
        return os.path.join(dir_path, f"{slug}_p{page_num}.html")

    # Load first page
    page_1_url = f"{base_url}?p=1&product_list_limit={product_list_limit}"
    page_1_html = fetch_or_load_html(page_file_path(1), page_1_url)
    tree = html.fromstring(page_1_html)

    # Extract total product count
    count_text = tree.xpath('//p[@id="toolbar-amount"]//span[@class="toolbar-number"]/text()')
    if not count_text or len(count_text) < 3:
        logging.warning("Could not determine total number of products.")
        return

    total_products = int(count_text[2].replace('\xa0', '').replace(',', ''))
    total_pages = ceil(total_products / product_list_limit)
    logging.info(f"{total_products} products found. Expecting {total_pages} pages.")

    # Fetch and save remaining pages
    for page in range(2, total_pages + 1):
        page_url = f"{base_url}?p={page}&product_list_limit={product_list_limit}"
        logging.info(f"Processing page {page}/{total_pages}: {page_url}")
        fetch_or_load_html(page_file_path(page), page_url)


def extract_slug(url):
    return urlparse(url).path.rstrip("/").split("/")[-1]


def get_path_parts(url: str) -> list:
    """Returns the non-empty parts of the URL path."""
    parsed = urlparse(url)
    return [part for part in parsed.path.strip('/').split('/') if part]

def get_parent_url(url: str) -> str:
    """Returns the parent URL by removing the last path segment."""
    parsed = urlparse(url)
    parts = get_path_parts(url)
    if parts:
        new_path = '/' + '/'.join(parts[:-1])
    else:
        new_path = '/'
    return f"{parsed.scheme}://{parsed.netloc}{new_path}"

def get_sub_path(url: str) -> str:
    """Returns the 'produits/vin' part from the URL."""
    parts = get_path_parts(url)
    return '/'.join(parts[1:-1]) if len(parts) > 2 else ''


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
        logging.warning(f"Max depth {max_depth} reached.")
        return []

    slug = extract_slug(url)
    dir_path = os.path.join(save_dir, slug)
    file_path = os.path.join(dir_path, f"{slug}.html")
    html_content = fetch_or_load_html(file_path, url)
    tree = html.fromstring(html_content)

    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]')
    if not items:
        logging.info("Leaf node reached (no items found).")
        return []

    items = items[0]
    parent_name, current_name, current_count = parse_breadcrumbs(items)
    logging.info(f"Parent: {parent_name}")
    logging.info(f"Current: {current_name} ({current_count})")

    if current_name and current_count:
        logging.info("Leaf node reached.")
        return []

    logging.info("Subcategory" if current_name else "Main category")

    categories = []
    for name, count, href in parse_subcategories(items):
        logging.info(f"Parsing subcategory: {name} ({count})")
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


def save_category_tree_json(categories, save_dir="run"):
    """Save the category tree to a JSON file in the specified directory."""
    os.makedirs(save_dir, exist_ok=True)
    output_path = os.path.join(save_dir, "category_tree.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    logging.info(f"Category tree saved to {output_path}")

def save_all_category_tree_pages(tree, save_dir="run"):
    for category in tree:
        dir_path = os.path.join(save_dir, get_sub_path(category['url']))
        logging.info(
            f"Saving all category pages for {category['name']} under {dir_path}..."
        )
        save_all_category_pages(category['url'], save_dir=dir_path)

        save_all_category_tree_pages(category['subcategories'], save_dir)

if __name__ == "__main__":
    save_dir = "run"
    setup_logging(save_dir)
    main_url = f"{BASE_URL}/fr/produits"

    logging.info("Starting category parsing...")
    tree = parse_categories_recursively(main_url, save_dir=save_dir)
    save_category_tree_json(tree, save_dir=save_dir)

    print("\nSAQ Category Tree:")
    print_category_tree(tree)

    # BEGIN_DEBUG
    # save_dir = "run/produits/spiritueux/vodka"
    # main_url = f"{BASE_URL}/fr/produits/spiritueux/vodka/vodka"
    # END_DEBUG
    save_all_category_tree_pages(tree)
