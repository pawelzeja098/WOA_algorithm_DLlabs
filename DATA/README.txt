Dobra to tak, data_source_school.csv to sa surowe dane zerzniete z open maps czy czegos takiego:
tu link ::: https://gis-support.pl/dane-do-pobrania/?fbclid=IwY2xjawQdJ4JleHRuA2FlbQIxMABicmlkETFHcmZIOWtTMUdrSE9adDRIc3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHsA2nhGM5I9DbsYtKujBAOMBJFuaJSrruNS_u3RtdN147BrjbFgt-5fpbGkW_aem_T_LWyrUrPVL9GwT7oojp4g
OPENSTREETMAP klikamy i macie
=========================================
szkoly_final to obrobione ladnie(moim zdaniem) i są tam:
x,y - wspolrzedne(do normalizacji)
nazwa 
powiat
gmina
postal_code
id

w pozostałych plikach lista gmin i powiatow, nie wszystkie gminy maja szkole jak cos (z 3 albo 4 tak dokładniej mowiac)

gminy.csv to wyciagniete gminy z pliku szkoły_final.csv

gminy_ready.csv jak się nie dziabnalem to zawiera wszystkie gminy z malopolski.
format powinien byc taki sam jak w szkoly_final tzn. gmina Nazwa gminy, chyba że to gmina miejska to wtedy po prostu np. Limanowa czyli mamy gmina Limanowa (wiochy) i Limanowa (miasto) proste łatwe i przyjemne. statystyki pododaje moze dzisiaj moze nie zobaczę jak mi się będzie chciało z tym kopac. i tez powiaty sa tam

powiaty.csv no lista powiatow - to trzeba uzupelnic o statystyki 