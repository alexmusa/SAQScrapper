import requests
r = requests.get("https://www.saq.com/webapp/wcs/stores/servlet/AjaxProduitSearchResultView?facetSelectionCommandName=SearchDisplay&searchType=&originalSearchTerm=*&orderBy=1&categoryIdentifier=06&showOnly=product&langId=-2&beginIndex=40&metaData=YWRpX2YxOjA8TVRAU1A%2BYWRpX2Y5OjE%3D&pageSize=20&catalogId=50000&searchTerm=*&pageView=&facet=&pageNumber=3&categoryId=39919&storeId=20002")

print(r.status_code)
print(r.headers)
print(r.content)