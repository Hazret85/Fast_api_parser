import requests
from bs4 import BeautifulSoup

urls = ['https://www.kinonews.ru/top100/','https://www.kinonews.ru/top100_p2/']

def parser_films(urls):
    result = {}
    for url in urls:
        HEADERS = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                   'User-agent':''}


        res = requests.get(url,headers=HEADERS)
        soup = BeautifulSoup(res.content,'lxml')

        titles = soup.findAll(class_='titlefilm')

        for film_info in titles:
            title = film_info.text
            descriptions = film_info.findNext(class_='rating_rightdesc')
            info_lst = []
            for info in descriptions:
                info = info.text.replace('\n','')
                if info != '':
                    info_lst.append(info)
            result[title] = info_lst



    return result

res = parser_films(urls)
print(res)

