import re
import unicodedata
import os
import time
import random
import json
import glob
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

def clean_extraneous_whitespace(text):
    # Strip leading/trailing whitespace and replace multiple spaces/tabs/newlines with a single space
    return re.sub(r'\s+', ' ', text).strip()

def normalize_price(price_str):
    """Remove non-breaking spaces and other unicode characters from price string and convert to float."""
    if not price_str:
        return None
    # Remove non-breaking spaces, regular spaces, and non-numeric characters except the dot
    cleaned = unicodedata.normalize("NFKD", price_str)
    cleaned = re.sub(r"[^\d.,]", "", cleaned).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError as e:
        raise e


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

def parse_products_from_html(html_content):
    """Extract product information from category page HTML."""
    tree = html.fromstring(html_content)
    product_elements = tree.xpath('//li[contains(@class, "product-item")]')

    products = {}

    for product in product_elements:
        def get(xpath_expr):
            return product.xpath(xpath_expr)

        def text(xpath_expr):
            return get(xpath_expr)[0].strip() if get(xpath_expr) else ''

        url = text('.//a[contains(@class,"product-item-link")]/@href')
        code_saq = text('.//div[@class="saq-code"]/span[last()]/text()')
        name = text('.//a[contains(@class,"product-item-link")]/text()')

        type_info = get('.//strong[contains(@class, "product-item-identity-format")]/span//text()')
        parts = [t.strip() for t in type_info if t.strip() and t.strip() != "|"]
        product_type = parts[0] if len(parts) > 0 else ''
        volume = parts[1] if len(parts) > 1 else ''
        country = parts[2] if len(parts) > 2 else ''

        rating = text('.//div[contains(@class,"rating-result")]/@title')
        rating_pct = int(rating.split(":")[1].replace("%", "").strip()) if ":" in rating else None
        reviews_text = text('.//div[@class="reviews-actions"]/a/text()')
        reviews_count = int(reviews_text.strip("()")) if reviews_text else 0

        discount_el = get('.//div[contains(@class,"product-item-discount")]/span/text()')
        discounted = bool(discount_el)
        discount_pct = discount_el[0].replace('%', '').strip() if discounted else None

        price = text('.//span[contains(@id, "product-price")]/span[@class="price"]/text()').replace('\xa0$', '').replace(',', '.')
        old_price_el = text('.//span[contains(@id, "old-price")]/span[@class="price"]/text()')
        old_price = old_price_el.replace('\xa0$', '').replace(',', '.') if old_price_el else price

        available_online = any("En ligne" in x for x in get('.//span[contains(@class,"in-stock")]/text()'))
        available_instore = any("En succursale" in x for x in get('.//span[contains(@class,"in-stock")]/text()'))
        
        # Final clean-up
        name = clean_extraneous_whitespace(name)
        volume = clean_extraneous_whitespace(volume)
        
        products[code_saq] = {
            "url": url,
            "code_saq": code_saq,
            "name": name,
            "type": product_type,
            "volume": volume,
            "country": country,
            "rating_pct": rating_pct,
            "reviews_count": reviews_count,
            "discounted": discounted,
            "discount_pct": discount_pct,
            "price": normalize_price(price),
            "old_price": normalize_price(old_price),
            "available_online": available_online,
            "available_instore": available_instore,
        }

    return products

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

def parse_all_saved_pages(base_dir="run", output_file="products.json"):
    """Parse all saved category pages and extract product data into a single JSON file."""
    all_products = {}
    page_files = glob.glob(os.path.join(base_dir, "**", "*_p*.html"), recursive=True)
    logging.info(f"Found {len(page_files)} category page files to parse.")

    for page_file in page_files:
        logging.info(f"Parsing file: {page_file}")
        try:
            with open(page_file, "r", encoding="utf-8") as f:
                html_content = f.read()
                products = parse_products_from_html(html_content)
                all_products = all_products | products
        except Exception as e:
            logging.error(f"Failed to parse {page_file}: {e}")

    output_path = os.path.join(base_dir, output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    logging.info(f"Saved {len(all_products)} products to {output_path}")

def parse_and_split_by_category(base_dir="run"):
    """Parse saved pages and write products to individual JSON files per category."""
    page_files = glob.glob(os.path.join(base_dir, "**", "*_p*.html"), recursive=True)
    logging.info(f"Found {len(page_files)} page files for splitting by category.")

    category_products = {}

    for page_file in page_files:
        try:
            with open(page_file, "r", encoding="utf-8") as f:
                html_content = f.read()
                products = parse_products_from_html(html_content)

                # Get relative category path from base_dir
                relative_path = os.path.relpath(page_file, base_dir)
                category_path = os.path.dirname(relative_path)

                if category_path not in category_products:
                    category_products[category_path] = []
                category_products[category_path].extend(products)
        except Exception as e:
            logging.error(f"Error parsing {page_file}: {e}")

    for category_path, products in category_products.items():
        file = extract_slug(category_path)
        output_path = os.path.join(base_dir, category_path, "products.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            # json.dump(products, f, ensure_ascii=False, indent=2)
            pass
        logging.info(f"Saved {len(products)} products to {output_path}")


if __name__ == "__main__":
    save_dir = "run"
    setup_logging(save_dir)
    main_url = f"{BASE_URL}/fr/produits"

    # logging.info("Starting category parsing...")
    # tree = parse_categories_recursively(main_url, save_dir=save_dir)
    # save_category_tree_json(tree, save_dir=save_dir)

    # print("SAQ Category Tree:")
    # print_category_tree(tree)

    # logging.info("Retrieving all products...")
    # save_all_category_tree_pages(tree)
    
    logging.info("Extracting all products...")
    parse_all_saved_pages()
    # parse_and_split_by_category()