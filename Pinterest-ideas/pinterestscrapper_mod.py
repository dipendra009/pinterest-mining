import sys
import os
import subprocess
# sys.path.append("C:\Python27\Lib\site-package")
from bs4 import BeautifulSoup
import urllib2
import requests
import urllib
from requests import session
import traceback
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from pyquery import PyQuery as pq

import time
import calendar
import re
import json
import random
from configobj import ConfigObj

# import pymongo
# from pymongo import MongoClient
# from pymongo.errors import DuplicateKeyError, OperationFailure, AutoReconnect

driver  =None

# import voxsup_lib.mongo
# from voxsup_lib.mongo import get_mongo_client_and_db as voxsup_get_mongo_client_and_db, insert_into_mongo as voxsup_insert_into_mongo, update_into_mongo as voxsup_update_into_mongo



def connect_to_mongo(config):
    mongo_host = config['mongo']['host_public'][
        0]  # random.choice(config['mongo']['host_public'])
    mongo_hosts = []
    mongo_hosts.append(mongo_host)
    # print mongo_host
    mongo_port = int(config['mongo']['port'])
    db = config['mongo']['db_pinterest']
    user = config['mongo']['user']
    passwd = config['mongo']['passwd']
    # print mongo_host," ",mongo_port," ",db," ",user
    mongo_client, mongo_db = voxsup_get_mongo_client_and_db(mongo_hosts,
                                                            mongo_port, db,
                                                            user, passwd)
    # print "mongo_client : ", mongo_client
    return (mongo_client, mongo_db)


def get_driver(path, driver_width=800, driver_height=800, limit=5):
    connections_attempted = 0
    global driver
    if driver != None:
        return driver
    while connections_attempted < limit:
        try:
            binary = FirefoxBinary(path);
            driver = webdriver.Firefox(
                firefox_binary=binary)  # PhantomJS(service_args=
            return driver
        except Exception as e:
            connections_attempted += 1
            print('Getting driver again...')
            print(' connections attempted: {}'.format(connections_attempted))
            # print "Error : ",e
            print(' exception message: {}'.format(e))
            traceback.print_exc()


def process_whole_page(path, entity, url, task1, task2, type_h, limit, email,
                       passwd, connections_to_attempt=5, scrolls_to_attempt=5,
                       sleep_interval=2):
    """
    Process the whole page at url with the given function, making sure
    that at least limit results have been processed -- or that there
    are less than limit results on the page.
    To do this, we scroll down the page with driver.
    Parameters
    ----------
    driver: selenium.webdriver
    url: string
    task1: function1
    task2: function2
    type_h: 0 - board, 1 - pins, 2 - followers, 3 - following
    Text fetched by driver is processed by this.
    Returns a list.
    limit: int
    Until we get this many results, or become certain that there
    aren't this many results at the url, we will keep scrolling the
    driver.
    connections_to_attempt: int
    scrolls_to_attempt: int
    sleep_interval: float
    Sleep this number of seconds between tries.
    Returns
    -------
    results: list or None
    Whatever the process function returns.
    Raises
    ------
    e: Exception
    If connection times out more than connections_to_attempt
    """
    assert (scrolls_to_attempt > 0)
    assert (limit > 0)
    print '\ncalled process whole page with path %s url %s task1 %s task2 %s ' \
          'type_h %s ' \
          'limit %s email %s password %s' % (
              path, url, str(task1), str(task2), str(type_h), str(limit),
              email, passwd)
    global driver
    connections_attempted = 0
    count = 0
    new_results = None
    results = None
    items_dict = dict()
    if driver is None:
        driver = get_driver(path)
        login_url = "https://www.pinterest.com/login/"
        driver.get(login_url)
        username = driver.find_element_by_name('username_or_email')
        username.send_keys(email)
        password = driver.find_element_by_name('password')
        password.send_keys(passwd)
        password.send_keys(Keys.RETURN);
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "usernameLink")))
        time.sleep(1)
    while connections_attempted < connections_to_attempt:
        try:
            if type_h != 1:
                login_url = "https://www.pinterest.com/login/"
                driver.get(login_url)
                username = driver.find_element_by_name('username_or_email')
                username.send_keys(email)
                password = driver.find_element_by_name('password')
                password.send_keys(passwd)
                password.send_keys(Keys.RETURN);
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                            (By.CLASS_NAME, "usernameLink")))
                time.sleep(1)
            # print "url:",url
            driver.get(url)

            driver.execute_script("return document.documentElement.outerHTML")

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # print soup
            # print "Getting count"
            if task1 != None:
                limit = task1(soup, entity)

            # limit = pin_count
            # print "Limit : ",limit
            results = task2(type_h, soup)  # get_pins(soup,entity)
            # print "Len of results = ",len(results)
            for r in results:
                if type_h > 1:
                    r = clean_up_user(r)
                if not items_dict.has_key(r):
                    items_dict[r] = 1
                # print r
            print "Data retrieved so far.. : ", len(items_dict)
            all_scrolls_attempted = 0
            connections_attempted += 1

            # If we fetch more than limit results already, we're done.
            # Otherwise, try to get more results by scrolling.
            # We give up after some number of scroll tries.
            # If we do get more results, then the scroll count resets.
            if len(results) < limit:
                scrolls_attempted = 0
                while (scrolls_attempted < scrolls_to_attempt and len(
                        results) < limit):
                    all_scrolls_attempted += 1
                    scrolls_attempted += 1

                    # Scroll and parse results again.
                    # The old results are still on the page, so it's fine
                    # to overwrite.
                    # print "Scroll :",scrolls_attempted
                    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    driver.execute_script(
                        "return document.documentElement.outerHTML")
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                    # WebDriverWait(driver,30).until(EC.presence_of_all_elements_located((By.CLASS_NAME,"ajax Grid Module")))
                    # print driver.text()
                    time.sleep(5)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    # print soup
                    # print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&"
                    new_results = task2(type_h, soup)  # get_pins(soup,entity)

                    if len(new_results) > len(results):
                        results = new_results
                        for r in results:
                            if type_h > 1:
                                r = clean_up_user(r)
                            if not items_dict.has_key(r):
                                items_dict[r] = 1
                                # print r
                        print "Data retrieved so far : ", len(items_dict)
                print(
                'Obtained {} results after {} scrolls'.format(len(items_dict),
                                                              all_scrolls_attempted))
            return items_dict
        except Exception as e:
            connections_attempted += 1
            print('URL failed: {}'.format(url))
            print(' connections attempted: {}'.format(connections_attempted))
            print(' exception message: {}'.format(e))
            traceback.print_exc()
            time.sleep(sleep_interval)
            # return pins_dict
            driver.close()
            driver.quit()
            driver = get_driver(path)
    #driver.close()
    #driver.quit()

    return items_dict


# def get_repins(page,pin_id):
#    soup = BeautifulSoup(page.read())
#    script_tag = soup.find("script",{"id" : "jsInit"})
#    blob = script_tag.extract().text
#    lines = blob.split("\n")
#    data = (lines[2]).strip()
#    # print data
#    count = 0
#    myre = re.compile(r'^\P.start.start\((.*)\);$')
#    result = myre.match(data)
#    repins = result.groups()[0]
#    repins_json = json.loads(repins)['resourceDataCache']
#    for r in repins_json:
#        #print json.dumps(r,indent=4,sort_keys = True)
#        if 'pin_id' in r['resource']['options']:
#            if r['resource']['options']['pin_id'] == pin_id:
#                for u in r['data']:
#                    print json.dumps(u,indent=4,sort_keys = True)
#                    count = count + 1
#                    print "-------------"
#    print "count = ",count
#  
#  
#  
# def get_user_likes(page,pin_id):
#    soup = BeautifulSoup(page.read())
#    script_tag = soup.find("script",{"id" : "jsInit"})
#    #print script_tag.extract().text
#    blob = script_tag.extract().text
#    lines = blob.split("\n")
#    data = (lines[2]).strip()
#   # print data
#    myre = re.compile(r'^\P.start.start\((.*)\);$')
#    result = myre.match(data)
#    users = result.groups()[0]
#    users_json = json.loads(users)['resourceDataCache']
#    #print users_json
#    user_likes = []
#    for u in users_json:
#        if 'pin_id' in u['resource']['options']:
#            if u['resource']['options']['pin_id'] == pin_id:
#                for uu in u['data']:
#                    print json.dumps(uu,indent=4,sort_keys = True)
#                    print "+++++++++++++++++++++++++++"
#                    user_likes.append(uu)
#    return user_likes


def get_pin_info(path, url, pin_id):
    print path
    print url
    print pin_id
    pin_details = None
    try_attempts = 5
    made_attempts = 0

    #while made_attempts < try_attempts:
    try:
        driver = get_driver(path)
        driver.get(url)
        print 'before soup'
        soup = BeautifulSoup(driver.page_source)
        # print driver.page_source
        # soup = BeautifulSoup(page.read())
        # print "soup = ",soup
        #BeautifulSoup(bs4, "lxml")
        script_tag = soup.find("script", {"id": "jsInit1"})
        # soup =  pq(driver.page_source)
        # print soup
        # p = soup("#jsInit1")
        # print p.text()
        # return
        # print "Script tag:",script_tag
        # print script_tag.extract().text
        if script_tag == None:
            driver.close()
            driver.quit()
            print('G URL failed: {}'.format(url))
            return pin_details

        blob = script_tag.extract().text

        lines = blob.split("\n")
        data = (lines[2]).strip()
        # print "Data = ",data
        # print "Type of data : ",type(data)
        myre = re.compile(r'^\P.startArgs = \{(.*)}\;$')
        result = myre.match(data)
        # print  result
        pin = "{" + result.groups()[0] + "}"
        # print pin
        # print "+++++++++++++"
        pin_json = json.loads(pin)['resourceDataCache']

        for b in pin_json:
            # print json.dumps(b,indent=4,sort_keys = True)
            # print "++++++++++++++++++++++++++++++++++++++"
            if 'id' in b['data']:
                if b['data']['id'] == pin_id:
                    # print json.dumps(b['data'],indent=4,sort_keys = True)
                    pin_details = b['data']
        driver.close()
        driver.quit()
    except Exception as e:
        print e
        print('G URL failed: {}'.format(url))

    # made_attempts += 1
    return pin_details


def get_pin_image_source(path, url, pin_id):
    print url
    #print pin_id
    pin_details = None
    try_attempts = 5
    made_attempts = 0

    #while made_attempts < try_attempts:
    try:
        driver = get_driver(path)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source)
        # print driver.page_source
        # soup = BeautifulSoup(page.read())
        # print "soup = ",soup
        #BeautifulSoup(bs4, "lxml")
        script_tag = soup.find("script", {"id": "jsInit1"})
        image_div = soup.find("div",{"class":"pinImageSourceWrapper"})

        if image_div == None:
            #driver.close()
            #driver.quit()
            print'Different pattern..failed...',url
            return pin_details
        image= image_div.find('img')
        print image['src']
        return image['src']
    except Exception as e:
        print e
        print('G URL failed: {}'.format(url))
    # made_attempts += 1
    return None

def get_pin_image_source_urlopen(path, url, pin_id):
    print url
    #print pin_id
    pin_details = None
    try_attempts = 5
    made_attempts = 0

    #source = urllib.urlopen(url).read()
    #soup = BeautifulSoup(source)
    #print soup
    #open('test.txt','w').write(str(soup))
    #sys.exit(0)
    # print driver.page_source
    # soup = BeautifulSoup(page.read())
    # print "soup = ",soup
    #BeautifulSoup(bs4, "lxml")
    #script_tag = soup.find("script", {"id": "jsInit1"})
    #image_div = soup.find("div",{"class":"pinImageSourceWrapper"})

    try:
        driver = get_driver(path)
        #driver.get(url)
        #data = urllib2.urlopen(url)
        #source = urllib.urlopen(url).read()
        #soup = BeautifulSoup(source)
        # print driver.page_source
        # soup = BeautifulSoup(page.read())
        # print "soup = ",soup
        #BeautifulSoup(bs4, "lxml")
        username = 'dipendra@u.northwestern.edu'
        password = 'LG65009'
        source= requests.get(url, auth=(username, password)).content
        #open('text.html','w').write(source)
        #print source
        soup = BeautifulSoup(source)
        script_tag = soup.find("script", {"id": "jsInit1"})
        #print script_tag
        payload = {'action': 'login','username': username,'password': password}

        with session() as c:
            c.post('https://www.pinterest.com/login/?referrer=home_page', data=payload)
            response = c.get(url)
            source = response.content
        soup = BeautifulSoup(source)
        image_div = soup.find("div",{"class":"pinImageSourceWrapper"})

        if image_div == None:
            #driver.close()
            #driver.quit()
            print'Different pattern..failed...',url
            return pin_details
        image= image_div.find('img')
        print image['src']
        return image['src']
    except Exception as e:
        print e
        print('G URL failed: {}'.format(url))
    # made_attempts += 1
    return None


def close_driver():
    global driver
    driver.close()
    driver.quit()

def get_board_info(url, board_url):
    board_details = None
    try:
        driver = get_driver()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source)
        # soup = BeautifulSoup(page.read())
        # print soup
        script_tag = soup.find("script", {"id": "jsInit"})
        # print script_tag
        # print script_tag.extract().text
        blob = script_tag.extract().text
        lines = blob.split("\n")
        data = (lines[2]).strip()
        # print data
        myre = re.compile(r'^\P.startArgs\((.*)\);$')
        result = myre.match(data)
        board = result.groups()[0]
        board_json = json.loads(board)['resourceDataCache']

        for b in board_json:
            # print json.dumps(b,indent=4,sort_keys = True)
            if 'board_url' in b['resource']['options']:
                if b['resource']['options']['board_url'] == board_url:
                    data = b['data']
                    for d in data:
                        if 'board' in d:
                            # print json.dumps(d['board'],indent=4,sort_keys = True)
                            board_details = d['board']
                            break
                            # print "++++++++++++++"
        driver.close()
        driver.quit()
    except Exception as e:
        print e
        print('URL failed: {}'.format(url))
    return board_details


def process_pins(soup):
    mydivs = soup.findAll("div", {"class": "item"})
    pin_ids = []
    for item in mydivs:
        holder = item.find("div", {"class": "pinHolder"})
        p_id = get_pin_id(holder)
        # print p_id
        pin_ids.append(p_id)
    return pin_ids


def get_pin_details(config, path, pin_ids):
    pin_details = []
    count_seen = 0
    count_not_seen = 0
    for p_id in pin_ids:
        #try:
        #client, db = pinsc.connect_to_mongo(config)
        #cursor_p = db['pins']
        #data = cursor_p.find({"id": p_id})
        #pin_info = data[0]
        #if pin_info != None:
        #	# print p_id," exists"
        #	count_seen = count_seen + 1
        #	if p_id['pinner']['domain_verified'] == False:
        #		client.close()
        #		continue
        #client.close()
        #except:
        url = "http://www.pinterest.com/pin/" + str(p_id) + "/"
        print "url = ",url
        pin_info = None
        pin_info = get_pin_image_source_urlopen(path, url, p_id)
        count_not_seen = count_not_seen + 1
        # print json.dumps(pin_info,indent=4,sort_keys = True)
        # print "++++++++"
        if pin_info != None:
            pin_details.append(pin_info)
            count_seen +=1

        # Restart firefox after obtaining 5 pins
        # Done to avoid memory crash with too many firefox instances running
        #if count_seen % 15 == 0:
        #	restart_firefox(path)
    # time.sleep(5)
    #print "Pins seen :", count_seen
    #print "Pins not seen : ", count_not_seen
    return pin_details


def get_repin_count():
    repin_count = 0
    for p_id in pin_ids:
        url = "http://www.pinterest.com/pin/" + str(p_id) + "/"
        print "url = ", url
        # page = urllib2.urlopen(url)
        pin_info = get_pin_info(url, p_id)


def get_pin_count(soup, entity):
    script_tag = soup.find("script", {"id": "jsInit"})
    # print script_tag.extract().text
    blob = script_tag.extract().text
    lines = blob.split("\n")
    data = (lines[2]).strip()
    # print data
    myre = re.compile(r'^\P.startArgs\((.*)\);$')
    result = myre.match(data)
    pins = result.groups()[0]
    pins_json = json.loads(pins)['resourceDataCache']
    pin_count = 0
    pins_array = []
    for b in pins_json:
        if 'username' in b['resource']['options']:
            if b['resource']['options']['username'] == entity:
                if 'username' in b['data']:
                    # print json.dumps(b['data'],indent=4,sort_keys = True)
                    pin_count = b['data']['pin_count']
                    # print "# Pins = ",pin_count
    return pin_count


def get_board_details(board_urls):
    board_details = []
    count = 0
    for b in board_urls:
        url = "http://www.pinterest.com" + str(b)
        # print "url = ",url

        # Restart firefox after obtaining 5 boards
        # Done to avoid memory crash with too many firefox instances running
        if count % 5 == 0:
            restart_firefox()
        board_info = None
        board_info = get_board_info(url, b)

        # print json.dumps(board_info,indent=4,sort_keys = True)
        # print "++++++++"
        if board_info != None:
            board_details.append(board_info)
            count = count + 1
    return board_details


def store_pins_boards(client, db, collection, documents):
    if len(documents) > 0:
        voxsup_insert_into_mongo(client, db, collection, documents)
    return


def store_docs(client, db, collection, documents):
    if len(documents) > 0:
        voxsup_insert_into_mongo(client, db, collection, documents)
    return


def get_entity_info(url, entity):
    # print url
    e_data = None
    try:
        driver = get_driver()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source)
        # soup = BeautifulSoup(page.read())
        # print soup
        script_tag = soup.find("script", {"id": "jsInit"})
        # print script_tag.extract().text
        blob = script_tag.extract().text
        lines = blob.split("\n")
        data = (lines[2]).strip()
        # print data
        myre = re.compile(r'^\P.startArgs\((.*)\);$')
        result = myre.match(data)
        pins = result.groups()[0]
        pins_json = json.loads(pins)['resourceDataCache']

        for p in pins_json:
            # print json.dumps(p,indent=4,sort_keys = True)
            if 'username' in p['resource']['options']:
                # if p['resource']['options']['username'] == entity:
                e_data = p[
                    'data']  # json.dumps(p['data'],indent=4,sort_keys = True)
                # print e_data
                break
        driver.close()
        driver.quit()
    except Exception as e:
        print e
        print('URL failed: {}'.format(url))

    return e_data


def get_follower_count(soup, entity):
    script_tag = soup.find("script", {"id": "jsInit"})
    # print script_tag.extract().text
    blob = script_tag.extract().text
    lines = blob.split("\n")
    data = (lines[2]).strip()
    # print data
    myre = re.compile(r'^\P.startArgs\((.*)\);$')
    result = myre.match(data)
    pins = result.groups()[0]
    pins_json = json.loads(pins)['resourceDataCache']
    follower_count = 0
    pins_array = []
    for b in pins_json:
        # print json.dumps(b,indent=4,sort_keys = True)

        if 'username' in b['resource']['options']:
            if b['resource']['options']['username'] == entity:
                if 'username' in b['data']:
                    # print json.dumps(b['data'],indent=4,sort_keys = True)
                    follower_count = b['data']['follower_count']
                    # print "# Pins = ",pin_count
    return follower_count


# def get_username(holder):
#    holder_a = holder.find_all("a",{"class":"userWrapper"})
#    #print holder_a
#    href = holder_a[0].get('href')
#    #myre = re.compile(r'^//$')
#    #result = myre.match(href)
#    #print result
#    #u_name = result.groups()[0]
#    #print u_name
#    return href

def get_pin_id(holder):
    holder_a = holder.find_all("a", {"class": "pinImageWrapper"})
    href = holder_a[0].get('href')
    p = re.findall('\d+', href)
    pin_id = p[0]
    return pin_id


def extract_info(type_h, holder):
    # print "In extract_info"
    item = None
    wrapper = None
    if type_h == 0:  # board
        wrapper = "boardLinkWrapper"
    elif type_h == 1:  # pin
        wrapper = "pinImageWrapper"
    elif type_h == 2 or type_h == 3 or type_h == 4:  # follower/following/likes
        wrapper = "userWrapper"
    elif type_h == 5:
        wrapper = "boardLinkWrapper"
    # print wrapper

    holder_a = holder.find("a", {"class": wrapper})
    # print "+++++"
    # print holder_a
    href = holder_a.get('href')
    if type_h == 1:
        p = re.findall('\d+', href)
        item = p[0]
    else:
        item = href
    # print item
    return item


# def process_users(soup):
#    mydivs = soup.findAll("div",{"class" : "item"})      
#    user_names = []
#    for item in mydivs:
#        holder = item.find("div",{"class" : "UserBase User Module gridItem"})
#        u_name = get_username(holder)
#        print u_name
#        user_names.append(u_name)
#    return user_names


def process_info(type_h, soup):
    # print "Processing info"
    # print soup
    item = None
    extractions = []
    wrapper_component = None
    mydivs = None
    if type_h == 0:  # board
        wrapper_component = "noContext Module draggable ajax Board boardCoverImage"  # "Board Module boardCoverImage"
    elif type_h == 1:  # pin
        wrapper_component = "Module Pin pinActionBarStickyContainer summary"  # "Module Pin summary"
    elif type_h == 2 or type_h == 3:  # follower/following
        wrapper_component = "Module User draggable gridItem"  # "draggable ajax User Module gridItem"
    elif type_h == 4:  # likes
        wrapper_component = "Module User draggable gridItem"  # "draggable User Module gridItem"
    elif type_h == 5:  # repins
        wrapper_component = "Board Module boardCoverImage draggable"  # "draggable Board Module boardCoverImage"#"Board Module boardCoverImage"
    # print wrapper_component
    # try:
    mydivs = soup.find_all("div", {"class": "item"})
    if mydivs != None:
        for item in mydivs:
            holder = None
            holder = item.find("div", {"class": wrapper_component})
            if type_h == 2 or type_h == 3:
                holder1 = item.find("div",
                                    {"class": "Module User gridItem draggable"})
                if holder == None:
                    holder = holder1
            elif type_h == 0:
                holder1 = item.find("div",
                                    {"class": "Module Board boardCoverImage"})
                if holder == None:
                    holder = holder1
            # print "Came before extract_info"
            # print holder
            if holder != None:
                # print "$$$$$$$$$$$$$$$"
                item = extract_info(type_h, holder)
                # print "item = ",item
                extractions.append(item)
    # print "Len of extractions : ",len(extractions)
    return extractions


def clean_up_user(user):
    myre = re.compile(r'^\/(.*)\/$')
    result = myre.match(user)
    clean_user = result.groups()[0]
    clean_user = clean_user.split("/")[0]
    # print "clean usr : ",clean_user
    clean_user = str(clean_user).strip("\n\r")
    return clean_user


def get_users(user_names, config):
    user_docs = []
    count = 0
    for u in user_names:
        # user = clean_up_user(u)
        # Restart firefox after getting info for 5 ysers
        # Done to avoid memory crash with too many firefox instances running
        if count % 5 == 0:
            restart_firefox()

        data = None
        f_data = None
        client, db = connect_to_mongo(config)
        cursor = db['users']
        cdata = cursor.find({"username": u})
        for c in cdata:
            data = c
        client.close()
        if data == None:
            url = "http://www.pinterest.com/" + u + "/"
            print url
            f_data = get_entity_info(url, u)
        else:
            print "User ", u, " exists in database"
            try:
                f_data = data
            except:
                print "Lost Cursor"
        if f_data != None:
            user_docs.append(f_data)
        count = count + 1

    return user_docs


def store_entity(client, db, collection, documents):
    if len(documents) > 0:
        voxsup_insert_into_mongo(client, db, collection, documents)
    return


def store_mapping_gterms_ids(config, collection1, collection2, documents, term):
    print "++++", term
    if not documents:
        return
    idlist = []
    for d in documents:
        if d['pinner']['domain_verified'] == True:
            print d['id']
            idlist.append(long(d['id']))
    curr_time = calendar.timegm(time.localtime())
    client, db = connect_to_mongo(config)
    voxsup_update_into_mongo(client, db, collection1, {"search_tuple": term},
                             {"pins": idlist})
    store_pins_boards(client, db, collection2, documents)
    client.close()
    return


def store_gterms_pids(config, collection1, collection2, collection3, documents,
                      term):
    client, db = connect_to_mongo(config)
    print "++++", term
    curr_time = calendar.timegm(time.localtime())

    if not documents:
        voxsup_update_into_mongo(client, db, collection3,
                                 {"search_tuple": term},
                                 {"timestamp": curr_time})
        client.close()
        return
    # term_id_list = []
    for d in documents:
        if d['pinner']['domain_verified'] == True:
            print "=======Verified Pin Id:", d['id']
            found_entry = db[collection1].find_and_modify(
                update={"$set": {"timestamp": curr_time}},
                query={"terms": term, "id": long(d['id'])})
            if found_entry == None:
                voxsup_insert_into_mongo(client, db, collection1,
                                         {"terms": term, "id": long(d['id']),
                                          "timestamp": curr_time},
                                         ignore_dupes=False)
                print "Creating a new entry"
            else:
                print "Updating Timestamp for existing entry"

            # Store all pins regardless of whether the pinner is verified
    store_pins_boards(client, db, collection2, documents)

    # Update timestamp of when the term query was used to get pins
    voxsup_update_into_mongo(client, db, collection3, {"search_tuple": term},
                             {"timestamp": curr_time})
    client.close()
    return


def update_document(client, db, collection, where={}, update={}):
    voxsup_update_into_mongo(client, db, collection, where, update)
    return


def store_mapping_of_ids(client, db, collection1, collection2, documents, iid,
                         type_f):
    u_list = []
    data = []
    # print "Len of Documents : ",len(documents)

    if not documents:
        return
    i = 0
    del_node_indices = []
    for d in documents:
        if not d:
            del_node_indices.append(i)
            i = i + 1
            continue
        # print d
        u_id = long(d['id'])
        u_list.append(u_id)
        i = i + 1
    # print "++++++++++++++++"
    if len(u_list) == 0:
        return
    for d in del_node_indices:
        del documents[d]
    # print "Len of Documents : ",len(documents)
    curr_time = calendar.timegm(time.localtime())
    # note: iid for followers/followering is user id and re_pinners/likers is pin_id
    if type_f == 0:
        data.append(
                {'id': long(iid), 'followers': u_list, 'unixtime': curr_time,
                 'follower_count': len(u_list)})
    elif type_f == 1:
        data.append(
                {'id': long(iid), 'following': u_list, 'unixtime': curr_time,
                 'following_count': len(u_list)})
    elif type_f == 2:
        data.append(
                {'id': long(iid), 're_pinners': u_list, 'unixtime': curr_time,
                 'repin_count': len(u_list)})
    elif type_f == 3:
        data.append({'id': long(iid), 'likers': u_list, 'unixtime': curr_time,
                     'like_count': len(u_list)})
    print data
    voxsup_insert_into_mongo(client, db, collection1,
                             data)  # map of uid-follower/ing or pid-repinners/likers
    voxsup_insert_into_mongo(client, db, collection2,
                             documents)  # users collection

    return


def readFile(fname):
    file = open(fname, "r")
    lines = file.readlines()
    entity = []
    for l in lines:
        e = str(l).strip("\r\n ")
        # print e
        entity.append(e)
    return entity


def entity_stats(entity, config):
    users_collection = "users"
    # restart_firefox()e
    entity_url = "http://www.pinterest.com/" + entity
    print entity_url
    entity_info = get_entity_info(entity_url, entity)
    e_data = []
    e_data.append(entity_info)
    iid = entity_info['id']
    pin_count = entity_info['pin_count']
    board_count = entity_info['board_count']
    follower_count = entity_info['follower_count']
    following_count = entity_info['following_count']
    print "pin_count:", pin_count
    # Store entity info
    print "######## Storing ", entity, " info #######"
    client, db = connect_to_mongo(config)
    store_entity(client, db, users_collection, e_data)
    client.close()
    return (iid, pin_count, board_count, follower_count, following_count)


def get_boards(entity, config, board_count, email, passwd):
    board_collection = "boards"

    # Get Boards
    print "######## Storing ", entity, " boards #######"
    restart_firefox()
    board_url = "http://www.pinterest.com/" + entity + "/boards/"
    print board_url
    print "board_count : ", board_count
    board_urls = process_whole_page(entity, board_url, None, process_info, 0,
                                    board_count, email, passwd)
    board_docs = get_board_details(board_urls)
    client, db = connect_to_mongo(config)
    store_pins_boards(client, db, board_collection, board_docs)
    client.close()
    del board_docs
    return


def get_pins(entity, config, pin_count, email, passwd):
    pin_collection = "pins"
    # Get Pins
    restart_firefox()
    print "######## Storing ", entity, " pins #######"
    pin_url = "http://www.pinterest.com/" + entity + "/pins/"
    print pin_url
    pin_ids = process_whole_page(entity, pin_url, None, process_info, 1,
                                 pin_count, email, passwd)
    pin_ids = pin_ids.keys()
    # process 1000 at a time
    start = 0
    len_ids = len(pin_ids)
    chunk = 1000
    if len_ids < chunk:
        end = len_ids
    else:
        end = chunk
    # if end > len_ids:
    #	end = len_ids
    pins = None
    while (start < len_ids):
        temp_ids = pin_ids[start:end]
        pins = get_pin_details(temp_ids)
        if pins != None:
            print "Pins Processed: ", len(pins)
        client, db = connect_to_mongo(config)
        store_pins_boards(client, db, pin_collection, pins)
        client.close()
        start = end
        end = end + chunk
        if end > len_ids:
            end = len_ids
    return len_ids


def get_followers(entity, config, iid, follower_count, email, passwd):
    follower_collection = "followers"
    users_collection = "users"
    # Get Followers
    restart_firefox()
    print "######## Storing ", entity, " followers #######"
    followers_url = "https://www.pinterest.com/" + entity + "/followers/"
    print followers_url
    usernames = process_whole_page(entity, followers_url, None, process_info, 2,
                                   follower_count, email, passwd)
    users = usernames.keys()

    start = 0
    len_ids = len(users)
    chunk = 1000
    if len_ids < chunk:
        end = len_ids
    else:
        end = chunk

    user_docs = None
    while (start < len_ids):
        print start, " | ", end, " | ", len_ids
        temp_users = users[start:end]
        user_docs = get_users(temp_users, config)
        if user_docs != None:
            print "users processed : ", len(user_docs)
        client, db = connect_to_mongo(config)
        store_mapping_of_ids(client, db, follower_collection, users_collection,
                             user_docs, iid, 0)
        client.close()
        start = end
        end = end + chunk
        if end > len_ids:
            end = len_ids
    return len_ids


def get_following(entity, config, following_count, email, passwd):
    following_collection = "following"
    users_collection = "users"
    # Get Following
    restart_firefox()
    print "######## Storing ", entity, " following #######"
    following_url = "https://www.pinterest.com/" + entity + "/following/"
    print followers_url
    usernames = process_whole_page(entity, following_url, None, process_info, 3,
                                   following_count, email, passwd)
    user_docs = get_users(usernames, config)
    client, db = connect_to_mongo(config)
    store_mapping_of_ids(client, db, following_collection, users_collection,
                         user_docs, iid, 1)
    client.close()
    return


def restart_firefox(path):
    subprocess.call(["killall", "firefox-bin"])
    # subprocess.call(["chmod","755","/tmp/tmp*"])
    # os.system("chmod 755 /tmp/tmp*/")
    # os.system("rm -r -f /tmp/tmp*/")
    subprocess.call("rm -rf /tmp/tmp*", shell=True)
    command = []
    command.append(path)
    command.append("&")
    subprocess.Popen(args=command)

    return


def process_repins(pin_ids, entity, config, email, passwd):
    users_collection = "users"
    pin_collection = "pins"
    repin_collection = "repins"
    for p in pin_ids:
        print "######## Gettings ", p, " repins #######"
        repin_url = "https://www.pinterest.com/pin/" + str(p) + "/repins/"
        repin_collection = "repins"
        usernames = process_whole_page(entity, repin_url, None, process_info, 5,
                                       1000, email,
                                       passwd)  # assume max_repins as 5K
        user_docs = get_users(usernames, config)
        total_docs = len(user_docs)
        print "Total repinner : ", len(user_docs)
        iid = long(p)
        client, db = connect_to_mongo(config)
        voxsup_update_into_mongo(client, db, pin_collection, {"id": p},
                                 {"repin_count": total_docs})
        store_mapping_of_ids(client, db, repin_collection, users_collection,
                             user_docs, iid, 2)
        client.close()
        restart_firefox()
    return


def process_likes(pin_ids, entity, config, email, passwd):
    users_collection = "users"
    like_collection = "likes"
    pin_collection = "pins"
    for p in pin_ids:
        print "######## Getting ", p, " likes #######"
        like_url = "https://www.pinterest.com/pin/" + str(p) + "/likes/"
        usernames = process_whole_page(entity, like_url, None, process_info, 4,
                                       1000, email, passwd)
        user_docs = get_users(usernames, config)
        total_docs = len(user_docs)
        print "Total likes for pin ", p, " : ", len(user_docs)
        iid = long(p)
        client, db = connect_to_mongo(config)
        voxsup_update_into_mongo(client, db, pin_collection, {"id": p},
                                 {"like_count": total_docs})
        store_mapping_of_ids(client, db, like_collection, users_collection,
                             user_docs, iid, 3)
        client.close()
        restart_firefox()
    return


def data_count():
    restart_firefox()
    entities = readFile('PinterestBrands.txt')
    count = 0

    for e in entities:
        if count % 5 == 0:
            restart_firefox()
        entity_url = "http://www.pinterest.com/" + e
        # print entity_url
        entity_info = get_entity_info(entity_url, e)
        if entity_info != None:
            # iid = entity_info['id']
            pin_count = entity_info['pin_count']
            board_count = entity_info['board_count']
            follower_count = entity_info['follower_count']
            following_count = entity_info['following_count']
            brand = entity_info['username']
            print brand, "\t", pin_count, "\t", board_count, "\t", follower_count, "\t", following_count
        else:
            print e


def guided_text(soup):
    text = []
    spans = soup.find_all('span', {'class': 'guideText'})
    for s in spans:
        text.append(s.text)
    return text


def existing_node_ids(client, db):
    cursor_t = db['gnodes']
    data = cursor_pins.find()
    nodes = []
    for d in data:
        nodes.append(d['node_id'], d['node_name'])
    return nodes


def main2():
    filename = sys.argv[1]
    task = int(sys.argv[2])
    pin_login = sys.argv[3]
    config = ConfigObj("twitter.cfg")
    # client,db= connect_to_mongo(config)
    login = "pin" + pin_login
    email = config[login]['email']
    passwd = config[login]['password']
    print "email :", email
    print "password :", passwd
    entities = readFile(filename)

    # entity = "hrdillon" # "americanai"https://www.pinterest.com/hrdillon/
    # url = "http://www.pinterest.com/" + entity
    # data = get_entity_info(url,entity)
    # print json.dumps(data,indent=4,sort_keys = True)
    for e in entities:
        iid, p_c, b_c, f1_c, f2_c = entity_stats(e, config)
        if task == 0:
            f = open(filename + "_time", "a")
            print e, " : Total boards : ", b_c
            t1 = time.time()
            retrieved_boards = get_boards(e, config, b_c, email, passwd)
            t2 = time.time()
            print e, " Retrived boards : ", retrieved_boards
            diff = t2 - t1
            print diff
            f.write(e + " : Took " + str(diff) + " seconds for " + str(
                retrieved_boards))
            f.write("--------------------------\n")
            f.close()
        if task == 1:
            f = open(filename + "_time", "a")
            print e, " : Total pins : ", p_c
            t1 = time.time()
            retrieved_pins = get_pins(e, config, p_c, email, passwd)
            t2 = time.time()
            print e, " Retrived pins : ", retrieved_pins
            diff = t2 - t1
            print diff
            f.write(e + " : Took " + str(diff) + " seconds for " + str(
                retrieved_pins))
            f.write("--------------------------\n")
            f.close()
        elif task == 2:
            f = open(filename + "_time", "a")
            print e, " : Total followers : ", f1_c
            t1 = time.time()
            retrieved_followers = get_followers(e, config, iid, f1_c, email,
                                                passwd)
            t2 = time.time()
            print e, " Retrived followers : ", retrieved_followers
            diff = t2 - t1
            print diff
            f.write(e + " : Took " + str(diff) + " seconds for " + str(
                retrieved_followers) + "\n")
            f.write("--------------------------\n")
            f.close()
            print "========================================"
            # db.close()
            # f.close()

url =  'http://www.pinterest.com/pin/107804984808847588/'
path='/Applications/Firefox.app/Contents/MacOS/firefox-bin'
pinid=107804984808847588
#get_pin_image_source(path,url,pinid)
