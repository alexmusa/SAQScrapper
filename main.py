from lxml import html
import requests

#### Parsing de la page de recherche ####
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

# Peut aussi être raccourci à l'image des expressions suivantes
product_urls = tree.xpath("div[@id='resultatRecherche']"
                          "/div[@class='wrapper-middle-rech']"
                          "/div[@class='resultats_product']"
                          "/div[@class='img']/a/@href")

for url in product_urls:
    print(url)
print('\n')

#### Parsing de la page du produit ####
page = requests.get(product_urls[0])

print(page.status_code)
print(page.headers)
# print(page.text)
print('\n')

tree = html.fromstring(page.content)

# <body onload="MM_preloadImages('/etc/designs/SAQ/images/header/menu-produits-o_fr.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_fr.png','/etc/designs/SAQ/images/header/menu-a-propos-o_fr.png','/etc/designs/SAQ/images/header/menu-produits-o_en.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_en.png','/etc/designs/SAQ/images/header/menu-a-propos-o_en.png')">
#   <div class="bg">
#       <div id="content" class="produit">
#           <div class="parbase wcscontainer">
#               <div style="overflow: hidden; " class="wcs-container">
#                   <div class="product-page">
#                       <div class="product-bloc-fiche">
#                           <div class="product-page-left">
#                               <div class="product-description">
### Contient la description courte en haut de page.


# <body onload="MM_preloadImages('/etc/designs/SAQ/images/header/menu-produits-o_fr.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_fr.png','/etc/designs/SAQ/images/header/menu-a-propos-o_fr.png','/etc/designs/SAQ/images/header/menu-produits-o_en.png','/etc/designs/SAQ/images/header/menu-conseils-et-accords-o_en.png','/etc/designs/SAQ/images/header/menu-a-propos-o_en.png')">
#   <div class="bg">
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


# "//div[@class='product-description']/*" seul fait l'affaire
description = tree.xpath("body/div[@class='bg']"
                         "/div[@id='content' and @class='produit']"
                         "/div[@class='parbase wcscontainer']"
                         "/div[@class='wcs-container']"
                         "/div[@class='product-page']"
                         "/div[@class='product-bloc-fiche']"
                         "/div[@class='product-page-left']"
                         "/div[@class='product-description']")[0]
# de même "//div[@id='details' and @class='tabspanel']//li" seul fait l'affaire
detailed_infos = tree.xpath("body/div[@class='bg']"
                            "/div[@id='content' and @class='produit']"
                            "/div[@class='parbase wcscontainer']"
                            "/div[@class='wcs-container']"
                            "/div[@class='product-page']"
                            "/div[@class='product-bloc-fiche']"
                            "/div[@class='product-page-left']"
                            "/div[@class='product-page-onglet-wrapper']"
                            "/div[@id='product-page-tab-box']"
                            "/div[@class='tabsbody']"
                            "/div[@id='details' and @class='tabspanel']//li")

### Création du produit ###
# Il est encore necessaire de retirer des espaces vides et traiter les caractères spéciaux.
# TODO: implémenter une fonction filtrant les éléments vides des listes retournées par xpath()
code_SAQ = description.xpath('//div[@class="product-description-row2"]/text()')[1].strip()
code_CUP = description.xpath('//div[@class="product-description-row2"]/text()')[2].strip()
product_name = description.xpath('//h1[@class="product-description-title"]/text()')[0]
product_type = description.xpath('//div[@class="product-description-title-type"]/text()')[0].strip().split(',')[0]
product_blabla = description.xpath('//div[@class="product-description-row5"]/p/text()')[0]

print("Code SAQ :" + code_SAQ)
print("Code CUP :" + code_CUP)
print("Nom :" + product_name)
print("Type :" + product_type)
print("Blabla :" + product_blabla)
print('-------------------------')

# Titre des caractéristiques détaillées //div[@id='details' and @class='tabspanel']//li/div[@class="left"]/span/text()
# Caractéristiques détaillées //div[@id='details' and @class='tabspanel']//li/div[@class="right"]/text()
# Il faut néanmoins vérifier que la caractéristique n'est pas un tableau :
# (//div[@id='details' and @class='tabspanel']//li/div[@class="right"])[6]/*/name() == "table"
# Auquel cas la traité différemment

for info in detailed_infos:
    name = info.xpath('div[@class="left"]/span/text()')[0].strip()
    if(all(element.tag != 'table' for element in info.xpath('div[@class="right"]/*'))):
        value = info.xpath('div[@class="right"]/text()')[0].strip()
    else:
        value = "C'est un tableau"

    print(name + " : " + value)
print('\n')