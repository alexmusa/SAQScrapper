"""
Programme récupérant l'information des pages du site de la SAQ.
"""
from scrapping import *
from parsing import *
from database import *

if __name__ == '__main__':
    searchpage = retrieve_searchpage("20", "40")
    product_urls = parse_products_urls(searchpage)

    for url in product_urls:
        print(url)

    for i in range(3):
        productpage = retrieve_productpage(product_urls[i])
        product = parse_product(productpage)

        print("Code SAQ : " + product.code_SAQ)
        print("Code CUP : " + product.code_CUP)
        print("Nom : " + product.name_)
        print("Type : " + product.type_)
        print('-------------------------')
        for info in product.infos:
            print(info[0] + " : " + info[1])
