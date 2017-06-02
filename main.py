"""
Programme récupérant l'information des pages du site de la SAQ.
"""
from scrapping import *
from parsing import *
import json
import os.path


def jdefault(o):
    return o.__dict__

def save_position( position ):
    f = open('status', 'w')
    f.write(str(position))
    f.close()

def load_position():
    f = open('status', 'r')
    pos = int(f.readline())
    f.close()
    return pos

def add_entry( product ):
    db_file = open('saq.json', 'a')
    obj_json = json.dumps(product, default=jdefault)
    db_file.write(obj_json + '\n')
    db_file.close()

if __name__ == '__main__':


    product_per_page = 100
    if os.path.exists("status"):
        position = load_position()
        current_page = position // product_per_page
    else:
        position = 0
        current_page = 0

    while True:
        searchpage = retrieve_searchpage(str(current_page * product_per_page),
                                         str(product_per_page))
        product_urls = parse_products_urls(searchpage)

        for i in range(position % product_per_page, len(product_urls)):
            url = product_urls[i]
            print(url)
            productpage = retrieve_productpage(url)
            product = parse_product(productpage)

            print("Code SAQ : " + product.code_SAQ)
            print("Code CUP : " + product.code_CUP)
            print("Nom : " + product.name_)
            print("Type : " + product.type_)
            print("Price : " + product.price)
            print('-------------------------')
            for info in product.infos:
                print(info[0] + " : " + str(info[1]))

            add_entry(product)

            position += 1
            save_position(position)

        current_page = position // product_per_page

        if is_last_searchpage(searchpage):
            break
