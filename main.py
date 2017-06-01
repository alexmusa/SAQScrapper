from scrapping import *
from parsing import *

if __name__ == '__main__':
    searchpage = retrieve_searchpage("0", "20")
    product_urls = parse_products_urls(searchpage)
    for i in range(3):
        productpage = retrieve_productpage(product_urls[i])
        parse_product(productpage)
