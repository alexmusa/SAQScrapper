import requests

def retrieve_searchpage( beginIndex, pageSize ):
    '''Récupère une page de recherche du site de la SAQ.

    Keyword arguments:
    beginIndex -- index de début de la page de recherche
    pageSize -- nombre de résultats de la page de recherche

    Returns: contenu de la page au format binaire

    '''
    page = requests.get("https://www.saq.com/webapp/wcs/stores/servlet/AjaxProduitSearchResultView?"
                        "facetSelectionCommandName=SearchDisplay"
                        "&searchType="
                        "&originalSearchTerm=*"
                        "&orderBy=2" #Ordre de la recherche (1 : Pertinence, 2 : A-Z)
                        "&categoryIdentifier=06"
                        "&showOnly=product"
                        "&langId=-2" #Langue (-2 : Français)
                        "&beginIndex=" + beginIndex + #Index de début des résultats
                        "&metaData="
                        "&pageSize=" + pageSize + #Nombre de résultat par page
                        "&catalogId=50000"
                        "&searchTerm=*" #Terme de la recherche
                        "&pageView=grid"
                        "&facet="
                        "&categoryId=39919"
                        "&storeId=20002"
                        "&orderByType=1"
                        "&filterFacet=")


    print(page.status_code)
    print(page.headers)

    return page.content

def retrieve_productpage( url ):
    '''Récupère une page de produit du site de la SAQ.

    Keyword arguments:
    url -- url de la page (string)

    Returns: contenu de la page au format binaire

    '''
    page = requests.get(url)

    print(page.status_code)
    print(page.headers)

    return page.content