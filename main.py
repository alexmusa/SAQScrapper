"""Programme récupérant l'information des pages du site de la SAQ.
Usage:
  saq.py --new
  saq.py --continue
  saq.py -h | --help
  saq.py --version
Options:
  -h --help     Show this screen.
  --version     Show version.
  --new         Commence une nouvelle collecte.
  --continue    Continue la dernière collecte.
"""
# Librairies
from docopt import docopt
from datetime import datetime
# Fonctions
from scrapping import *
from parsing import *
from dao import *
# Autres
from status import *
import os.path
import sys

PRODUCTS_PER_PAGE = 100
MAX_ATTEMPTS = 10

if __name__ == '__main__':
    arguments = docopt(__doc__, version='SAQ Scrapper 0.1')

    if arguments['--new']:
        Status.state = 'STARTING'
        Status.beginDate = datetime.now().strftime(DATE_FORMAT)
        Status.endDate = ''
        Status.position = 0
        save_status()
    elif arguments['--continue']:
        if os.path.exists("status"):
            load_status()
            if Status.state == 'FINISHED':
                message = "Nothing to do. Script will exit"
                write_log(5, message)
                sys.exit(message)
        else:
            message = "Cannot find status file. Script will exit"
            write_log(5, message)
            sys.exit(message)

    current_page = Status.position // PRODUCTS_PER_PAGE

    Status.state = 'RUNNING'
    save_status()

    while True:
        write_log(6, "Retrieving page #{0} ({1} per page)"
                  .format(str(current_page * PRODUCTS_PER_PAGE), str(PRODUCTS_PER_PAGE)))
        essais = 0
        success = False
        while(not success):
            try:
                searchpage = retrieve_searchpage(str(current_page * PRODUCTS_PER_PAGE),
                                                 str(PRODUCTS_PER_PAGE))
                success = True
            except requests.exceptions.RequestException as err:
                essais += 1
                write_log(3, err)
                if essais > MAX_ATTEMPTS:
                    message = "Coulnd't retrieve page after {} attempts".format(essais)
                    write_log(3, message)
                    sys.exit(message)
            except Exception as e:
                message = "Unexpected error: {0}".format(e)
                write_log(2, message)
                sys.exit(message)

        try:
            product_urls = parse_products_urls(searchpage)
        except Exception as e:
            write_log(4, "Couldn't parse {0}: {1}".format(url, e))

        for i in range(Status.position % PRODUCTS_PER_PAGE, len(product_urls)):
            url = product_urls[i]
            print(url)

            write_log(6, "Retrieving " + url)
            essais = 0
            success = False
            while (not success):
                try:
                    productpage = retrieve_productpage(url)
                    success = True
                except requests.exceptions.RequestException as err:
                    essais += 1
                    write_log(3, err)
                    if essais > MAX_ATTEMPTS:
                        message = "Coulnd't retrieve page after {} attempts".format(essais)
                        write_log(3, message)
                        sys.exit(message)
                except Exception as e:
                    message = "Unexpected error: {0}".format(e)
                    write_log(2, message)
                    sys.exit(message)

            try:
                product = parse_product(productpage)
            except Exception as e:
                write_log(4, "Couldn't parse {0}: {1}".format(url, e))

            print("Code SAQ : " + product.code_SAQ)
            print("Code CUP : " + product.code_CUP)
            print("Nom : " + product.name_)
            print("Type : " + product.type_)
            print("Price : " + product.price)
            print('-------------------------')
            for info in product.infos:
                print(info[0] + " : " + str(info[1]))

            add_entry(product)

            Status.position += 1
            save_status()

        if is_last_searchpage(searchpage):
            break

    Status.state = 'FINISHED'
    Status.endDate = datetime.now().strftime(DATE_FORMAT)
    save_status()
    sys.exit(0)