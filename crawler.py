from datetime import datetime
from time import sleep
import requests
from bs4 import BeautifulSoup
from satl import Satl

import re
import json
from utils.printer import printer
import os
import csv

base_url = 'https://www.tripadvisor.com'
top_activity_url = base_url + '/Attractions-%s-%sActivities-%s.html'
# top_restaurants_url = base_url + '/Restaurants-%s-%sActivities-%s.html'

cities=[
    {'index': 'g316021', 'city': 'Shiraz','country': 'Iran'},
    {'index': 'g293999', 'city': 'tehran','country': 'Iran'},
    {'index': 'g2189612', 'city': 'Mashhad','country': 'Iran'},
    {'index': 'g295423', 'city': 'Isfahan','country': 'Iran'},
    {'index': 'g644373', 'city': 'Kish','country': 'Iran'},
    {'index': 'g303961', 'city': 'Tabriz','country': 'Iran'},
    {'index': 'g303962', 'city': 'Yazd','country': 'Iran'},
    {'index': 'g3532582', 'city': 'Gilan','country': 'Iran'},
    {'index': 'g672716', 'city': 'Hamadan','country': 'Iran'},
    {'index': 'g1536391', 'city': 'Kermanshah','country': 'Iran'},
    {'index': 'g1047018', 'city': 'Mazandaran','country': 'Iran'}
]

def get_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0'
    }
    printer('blue', 'Get', url)
    try:
        html = requests.get(url, headers=headers)
    except:
        pass
    sleep(1)
    soup = BeautifulSoup(html.content, 'html.parser')
    return soup


def get_text(item):
    if item:
        return item.get_text()
    return ''


def get_poi(url, data_dict, crawler_list, kind):
    page = get_page(url)
    jsons=page.find("script",type="application/ld+json")
    dataj = json.loads(jsons.string)
    # print(dataj['@type'])

    # data_dict['name'] = dataj['name']
    data_dict['images'] = dataj['image']
    data_dict['url'] = url

    # dir = os.getcwd() + os.sep+'tripAdvisorData/'+dataj['address']['addressLocality']  # save directory
    # if not os.path.exists(dir):
    #     os.makedirs(dir)
 
    return data_dict


def get_poi_list(url, crawler_list, kind):
    pois = []
    page = get_page(url)
    if kind == 'things-to-do':
        jsons=page.find_all("script",type="application/ld+json")
        for j in jsons:        
            dataj = json.loads(j.string)
            typej=dataj['@type']
            if typej=='ItemList':
                items=dataj['itemListElement']
            
    else:
        items = page.find_all('div', id=lambda x: x and x.startswith('eatery_'))
    # print(dataj)

    for item in items:
        poi = {'name': item['name']}
        url = base_url +item['url']

        if is_exists(url):
            continue
        poi_data = ''
        if url.endswith('html.html'):
            printer('yellow', 'Not download', url)
            continue
        try:
            poi_data = get_poi(url, poi, crawler_list, kind)
        except Exception as e:
            msg = '%s - %s' % (url, e)
            printer('red', 'Error', msg)
        if poi_data:
            # set_data(poi_data)
            pois.append(poi_data)

    return pois


def make_pages_and_normalize_input(loop, keys):
    if loop == 0:
        page = ''
    else:
        page = 'oa%s-' % (loop * 30)

    if 'state' in keys:
        state = keys['state']
    else:
        state = keys['country']

    printer('green', 'Country', keys['country'])

    if 'name' in keys:
        name = keys['name']
    else:
        name = keys['country']

    return page, state, name


def crawl_things_to_do_city(keys):
    list_dict=[]
    for x in range(0, 3):
        page, state, name = make_pages_and_normalize_input(x, keys)
        url = top_activity_url % (keys['index'], page, name)
        dictt=get_poi_list(url, keys, 'things-to-do')
        list_dict.extend(dictt)
    return list_dict


def get_thingsToDo_city(keys):
    return crawl_things_to_do_city(keys)


def is_exists(url):
    return Satl.is_exists(url)


def set_data(data):
    # if is_exists(data['url']):
    #     return False
    data['create_date'] = datetime.now()
    data['updated'] = False
    satl = Satl(data['url'], data=data)
    printer('magenta', 'Save', " %s - %s" % (satl.pk, satl.get('name')))
    satl.save()
    

    # this part writen beacuse of update images
    # else:
    #     satl = Satl(data['url']).load()
    return False

def download_uri(cities):
    for item in cities:
        with open('data/csv/'+item['city']+'.csv', 'r') as csvfile:
            dir = os.getcwd() + os.sep+'data/images/'+item['city']  # save directory
            if not os.path.exists(dir):
                os.mkdir(dir)
            csvfile.readline()
            lines=csvfile.readlines()
            for l in lines:
                a=l.split(',')
                name=a[0]
                uri=a[1]
                if os.path.isfile(dir+'/' +name+'_'+ uri.split('/')[-1]):
                    return
                else:    
                    with open(dir+'/' +name+'_'+ uri.split('/')[-1], 'wb') as f:
                        f.write(requests.get(uri, stream=True).content)
                        print(uri)
 
def main():    
    for item in cities:
        poi_list=get_thingsToDo_city(item)
        try:
            dir = os.getcwd() + os.sep+'data/csv/'+item['city']+'.csv'  # save directory
            with open(dir, 'w',newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=poi_list[0].keys())
                writer.writeheader()
                for d in poi_list:
                    writer.writerow(d)
        except IOError:
            print("I/O error")

if __name__ == "__main__":
    main()
    download_uri(cities)





# https://www.tripadvisor.com/Attractions-g293999-Activities-Tehran_Tehran_Province.html
# https://www.tripadvisor.com/Tourism-g316021-Shiraz_Fars_Province-Vacations.html
# https://www.tripadvisor.com/Tourism-g2189612-Mashhad_Razavi_Khorasan_Province-Vacations.html
# https://www.tripadvisor.com/Attractions-g295423-Activities-Isfahan_Isfahan_Province.html
# https://www.tripadvisor.com/Tourism-g644373-Kish_Island_Hormozgan_Province-Vacations.html
# https://www.tripadvisor.com/Tourism-g303961-Tabriz_East_Azerbaijan_Province-Vacations.html
# https://www.tripadvisor.com/Tourism-g303962-Yazd_Yazd_Province-Vacations.html
# https://www.tripadvisor.com/Attractions-g3532582-Activities-Gilan_Province.html
# https://www.tripadvisor.com/Attractions-g672716-Activities-Hamadan_Hamedan_Province.html
# https://www.tripadvisor.com/Attractions-g1536391-Activities-Province_of_Kermanshah.html
# https://www.tripadvisor.com/Attractions-g1047018-Activities-Mazandaran_Province.html    