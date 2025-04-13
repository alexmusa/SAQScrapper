import os
from lxml import html
import pytest
from saq_crawler.saq_crawler import (
    parse_breadcrumbs,
    parse_subcategories,
    parse_categories_recursively,
)


TEST_DIR = "tests/test_pages"


def load_test_html(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return html.fromstring(f.read())

# test_pages should contain:
# - Vin (7751)
#   - Vin rouge (4758)
#   - Vin blanc (2738) --- 2737 on vin-blanc.html
#   - Vin rosé (255)
# [...]
# - Cooler et cocktail prémixé (264)
#   - Cooler à base de spiritueux (223)
#   - Cocktail à base de spiritueux (18)
#   - Cocktail et cooler au vin (16)
#     - Cooler au vin (15)
#     - Sangria (1)
#   - Cocktail au cidre (7)
# [...]
@pytest.mark.parametrize("relative_path, expected_parent, expected_current, expected_count", [
    ("produits/vin/vin.html", "Autres catégories", "Vin", ""),
    ("produits/vin/vin-blanc/vin-blanc.html", "Vin", "Vin blanc", 2737),
    ("produits/cooler-et-cocktail-premixe/cocktail-et-cooler-au-vin/cooler-au-vin/cooler-au-vin.html", 
        "Cocktail et cooler au vin", "Cooler au vin", 15),
])
def test_parse_breadcrumbs(relative_path, expected_parent, expected_current, expected_count):
    filepath = os.path.join(TEST_DIR, relative_path)
    tree = load_test_html(filepath)
    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]')[0]
    parent, current, count = parse_breadcrumbs(items)

    assert parent == expected_parent
    assert current == expected_current
    assert str(count) == str(expected_count)


@pytest.mark.parametrize("relative_path, expected_first_child", [
    ("produits/vin/vin.html", ("Vin rouge", 4758, "https://www.saq.com/fr/produits/vin/vin-rouge")),
    ("produits/cooler-et-cocktail-premixe/cocktail-et-cooler-au-vin/cocktail-et-cooler-au-vin.html", 
        ("Cooler au vin", 
        15, 
        "https://www.saq.com/fr/produits/cooler-et-cocktail-premixe/cocktail-et-cooler-au-vin/cooler-au-vin")),
])
def test_parse_subcategories(relative_path, expected_first_child):
    filepath = os.path.join(TEST_DIR, relative_path)
    tree = load_test_html(filepath)
    items = tree.xpath('//ol[@class="items" and @data-action="gtm-cat-filters-parent"]')[0]

    children = parse_subcategories(items)
    assert children, "Subcategories should not be empty"
    name, count, url = children[0]
    expected_name, expected_count, expected_url = expected_first_child

    assert name == expected_name
    assert count == expected_count
    assert url == expected_url


def test_parse_categories_recursively_from_files():
    """Tests the recursive parser in a file-only context."""
    root_url = "https://www.saq.com/fr/produits/vin"
    result = parse_categories_recursively(
        url=root_url,
        save_dir=TEST_DIR,
        max_depth=2,
    )
    assert isinstance(result, list)
    assert all("name" in cat and "subcategories" in cat for cat in result)
    assert result[0]["name"] == "Vin rouge"  # Example: first child
