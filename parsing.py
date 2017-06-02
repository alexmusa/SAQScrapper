"""
Module parsant les pages du site de la SAQ.
"""
from lxml import html
from product import *

def is_last_searchpage( page ):
    tree = html.fromstring(page)

    icon = tree.xpath("div[@class='wrapper-top-rech']"
                       "/div[@class='PagerResultat']"
                       "/a/*[@title='Page suivante']")

    if icon:
        return False
    else:
        return True


def parse_products_urls( page ):
   '''Parse une page de recherche du site de la SAQ pour en extraire les urls des produits.

    Keyword arguments:
    page -- contenu de la page

    Returns: liste de strings

    '''
   tree = html.fromstring(page)

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
                             "/div[contains(concat(' ', normalize-space(@class), ' '), ' resultats_product ')]"
                             "/div[@class='img']/a/@href")

   return product_urls

def parse_product( page ):
    '''Parse une page de produit du site de la SAQ pour en extraire les informations sur le produit.

    Keyword arguments:
    page -- contenu de la page

    Returns:

    '''
    ##### Parsing de la page du produit #####
    tree = html.fromstring(page)

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


    # "//div[@class='product-description']/*" seul ferait l'affaire
    description = tree.xpath("body/div[@class='bg']"
                             "/div[@id='content' and @class='produit']"
                             "/div[@class='parbase wcscontainer']"
                             "/div[@class='wcs-container']"
                             "/div[@class='product-page']"
                             "/div[@class='product-bloc-fiche']"
                             "/div[@class='product-page-left']"
                             "/div[@class='product-description']")[0]
    # de même "//div[@id='details' and @class='tabspanel']//li" seul ferait l'affaire
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

    price = tree.xpath("body/div[@class='bg']"
                        "/div[@id='content' and @class='produit']"
                        "/div[@class='parbase wcscontainer']"
                        "/div[@class='wcs-container']"
                        "/div[@class='product-page']"
                        "/div[@class='product-bloc-fiche']"
                        "/div[@class='product-page-right']"
                        "/div[@class='product-add-to-cart-wrapper']"
                        "//p[@class='price']/text()")[0].strip()

    ### Création du produit ###
    # Il est encore necessaire de retirer des espaces vides et traiter les caractères spéciaux.
    # TODO: implémenter une fonction filtrant les éléments vides des listes retournées par xpath()
    # TODO: traiter le blabla à part car souvent non-défini
    code_SAQ = description.xpath('//div[@class="product-description-row2"]/text()')[1].strip()
    code_CUP = description.xpath('//div[@class="product-description-row2"]/text()')[2].strip()
    product_name = description.xpath('//h1[@class="product-description-title"]/text()')[0]
    product_type = description.xpath('//div[@class="product-description-title-type"]/text()')[0].strip().split(',')[0]
    paragraphe = description.xpath('//div[@class="product-description-row5"]/p/text()')

    product = Product(code_SAQ, code_CUP, product_name, product_type, price, paragraphe)

    # Titre des caractéristiques détaillées
    # //div[@id='details' and @class='tabspanel']//li/div[@class="left"]/span/text()
    # Caractéristiques détaillées
    # //div[@id='details' and @class='tabspanel']//li/div[@class="right"]/text()
    #
    # Il faut néanmoins vérifier que la caractéristique n'est pas un tableau, c'est-à-dire si un des éléments
    # de //div[@id='details' and @class='tabspanel']//li/div[@class="right"]/* à le tag "table".
    # Auquel cas ce tableau est sérialisé en JSON

    for info in detailed_infos:
        name = info.xpath('div[@class="left"]/span/text()')[0].strip()
        if all(element.tag != 'table' for element in info.xpath('div[@class="right"]/*')):
            value = info.xpath('div[@class="right"]/text()')[0].strip()
        else:
            table = []
            for element in info.xpath('div[@class="right"]/table/tr'):
                table.append([element.xpath('td[@class="col1"]/text()'), element.xpath('td[@class="col2"]/text()')])
            value = table

        product.add_info([name, value])

    return product