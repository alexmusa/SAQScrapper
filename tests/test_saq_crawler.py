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


@pytest.mark.parametrize("relative_path, expected_parent, expected_current, expected_count", [
    ("vin/vin.html", "Produits", "Vin", ""),
    ("vin/blanc/blanc.html", "Vin", "Vin blanc", ""),
    ("vin/blanc/france/france.html", "Vin blanc", "France", ""),
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
    ("vin/vin.html", ("Vin rouge", 5541, "/fr/produits/vin/vin-rouge")),
    ("vin/vin-blanc/vin-blanc.html", ("France", 1573, "/fr/produits/vin/vin-blanc/france")),
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
    root_url = "/fr/produits/vin"
    result = parse_categories_recursively(
        url=root_url,
        save_dir=TEST_DIR,
        max_depth=2,
    )
    assert isinstance(result, list)
    assert all("name" in cat and "subcategories" in cat for cat in result)
    assert result[0]["name"] == "Vin rouge"  # Example: first child
