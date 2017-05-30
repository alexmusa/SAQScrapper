from lxml import html
import requests
page = requests.get("https://www.saq.com/webapp/wcs/stores/servlet/AjaxProduitSearchResultView?"
                    "facetSelectionCommandName=SearchDisplay"
                    "&searchType="
                    "&originalSearchTerm=*"
                    "&orderBy=1"
                    "&categoryIdentifier=06"
                    "&showOnly=product"
                    "&langId=-2"
                    "&beginIndex=0"
                    "&metaData=YWRpX2YxOjA8TVRAU1A%2BYWRpX2Y5OjE%3D"
                    "&pageSize=100"
                    "&catalogId=50000"
                    "&searchTerm=*"
                    "&pageView="
                    "&facet="
                    "&pageNumber=3"
                    "&categoryId=39919"
                    "&storeId=20002")

print(page.status_code)
print(page.headers)
#print(page.content)
print('\n')

tree = html.fromstring(page.content)

# <div class="wrapper-top-rech"> pour les changements de page

# <div class="ColD affichageMozaique" id="resultatRecherche">
#   <div class="wrapper-middle-rech">
### Les résultats sont alors en ordre croissant.
#       <div id="result_41" class="resultats_product">
#           <div class ="img">
#               <a id = "productDisplayImageLink_873257" href = [...]
### Cette attribut href est l'url de la fiche produit.

product_urls = tree.xpath("div[@id='resultatRecherche']"
                  "/div[@class='wrapper-middle-rech']"
                  "/div[@class='resultats_product']"
                  "/div[@class='img']/a/@href")

for url in product_urls:
    print(url)
print('\n')

page = requests.get(product_urls[0])

print(page.status_code)
print(page.headers)
#print(page.content)
print('\n')

tree = html.fromstring(page.content)

product_urls = tree.xpath("div[@id='resultatRecherche']"
                          "/div[@class='wrapper-middle-rech']"
                          "/div[@class='resultats_product']"
                          "/div[@class='img']/a/@href")