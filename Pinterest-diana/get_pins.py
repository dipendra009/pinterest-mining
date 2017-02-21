import sys
import time
import urllib
import urllib2
from bs4 import BeautifulSoup
from configobj import ConfigObj
import pinterestscrapper_mod as pinsc

def main():
	  
    pin_login = '1'#sys.argv[1]

    #create config obj for list of configuration
    config = ConfigObj("./pinterest.cfg")
    path = config['firefox_path']
    print "firefox_path:",path

    #Pinterest login credentials for scraping
    login = "pin"+pin_login
    email = config[login]['email']
    passwd = config[login]['password']
    print "email :",email," password :",passwd

    pinsc.restart_firefox(path)

    pin_dict = dict()
    #scrape pins for each search_term
    search_terms = ["womans","shoes men smart","red flowers"]
    for s in search_terms:

        try:
            new_s = urllib.quote(s.decode('utf-8').encode('latin-1'))
        except:
            new_s = s
        #s = search['search_tuple']
        print "******************",s,"******************"
        pin_url = 'http://www.pinterest.com/search/?q='+new_s
        print pin_url
        sys.exit(0)
        pin_ids = pinsc.process_whole_page(path,None,pin_url,None,
                                           pinsc.process_info,1,10,email,passwd)
        print "Number of pins :",len(pin_ids)

        ##FAILS AFTER THIS
        pins = pinsc.get_pin_details(config,path,pin_ids.keys())
        for p in pins:
            print p
        pin_dict[s] = pins
    pinsc.close_driver()

    open('output.txt','w').write(str(pin_dict))

if __name__ == '__main__':
  main()
