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
#print(page.text)
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
# print(page.text)
print('\n')

tree = html.fromstring(page.content)

# <html xml:lang="fr" lang="fr">
#   <body onload="MM_preloadImages('/etc/designs/SAQ/images/header/menu-produits-o_fr.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_fr.png','/etc/designs/SAQ/images/header/menu-a-propos-o_fr.png','/etc/designs/SAQ/images/header/menu-produits-o_en.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_en.png','/etc/designs/SAQ/images/header/menu-a-propos-o_en.png')">
#       <div id="content" class="produit">
#           <div class="parbase wcscontainer">
#               <div style="overflow: hidden; " class="wcs-container">
#                   <div class="product-page">
#                       <div class="product-bloc-fiche">
#                           <div class="product-page-left">
#                               <div class="product-description">
### Contient la description courte en haut de page.


# <html xml:lang="fr" lang="fr">
#   <body onload="MM_preloadImages('/etc/designs/SAQ/images/header/menu-produits-o_fr.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_fr.png','/etc/designs/SAQ/images/header/menu-a-propos-o_fr.png','/etc/designs/SAQ/images/header/menu-produits-o_en.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_en.png','/etc/designs/SAQ/images/header/menu-a-propos-o_en.png')">
#       <div id="content" class="produit">
#           <div class="parbase wcscontainer">
#               <div style="overflow: hidden; " class="wcs-container">
#                   <div class="product-page">
#                       <div class="product-bloc-fiche">
#                           <div class="product-page-left">
#                               <div class="product-page-onglet-wrapper">
#                                   <div id="product-page-tab-box">
#                                       <div class="tabsbody">
#                                           <div id="details" class="tabspanel" role="tabpanel" aria-hidden="true" aria-labelledby="tab-details">
### Contient la description détaillé en bas de page.



description = tree.xpath("html/body/div[@class='bg']"
                         "/div[@id='content' and @class='produit']"
                         "/div[@class='parbase wcscontainer']"
                         "/div[@class='wcs-container']"
                         "/div[@class='product-page']"
                         "/div[@class='product-bloc-fiche']"
                         "/div[@class='product-page-left']"
                         "/div[@class='product-description']/@class")

detailed_infos = tree.xpath("html/body/div[@class='bg']"
                            "/div[@id='content' and @class='produit']"
                            "/div[@class='parbase wcscontainer']"
                            "/div[@class='wcs-container']"
                            "/div[@class='product-page']"
                            "/div[@class='product-bloc-fiche']"
                            "/div[@class='product-page-left']"
                            "/div[@class='product-page-onglet-wrapper']"
                            "/div[@id='product-page-tab-box']"
                            "/div[@class='tabsbody']"
                            "/div[@id='details' and @class='tabspanel']/@class")
print(description)
print('\n')

print(detailed_infos)
print('\n')