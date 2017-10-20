"""
Programme récupérant l'information des pages du site de la SAQ.
"""
from scrapping import *
from parsing import *
from dao import *
import os.path

if __name__ == '__main__':


    product_per_page = 100
    if os.path.exists("status"):
        position = load_position()
        current_page = position // product_per_page
    else:
        position = 0
        current_page = 0

    while True:

        categoriespage = retrieve_categoriespage()
        categories = parse_categories(categoriespage)
        # TODO: Sauvegarder ensuite les catégories

        for category in categories:
            # TODO: Modifier la fonction retrieve_searchpage pour
            # qu'elle prenne la categorie en paramètre
            searchpage = retrieve_searchpage(str(current_page * product_per_page),
                                             str(product_per_page))
            product_urls = parse_products_urls(searchpage)

            for i in range(position % product_per_page, len(product_urls)):
                url = product_urls[i]
                print(url)

                # retries = 0
                # success = False
                # while(retries < 100 and not success):
                #     try:
                productpage = retrieve_productpage(url)
                    # except Exception as e:
                    #     retries += 1
                    #     write_log(e)
                    # else:
                    #     success = True

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
