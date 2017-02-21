from bs4 import BeautifulSoup
from urllib import urlopen
import urllib
from utils import *
from selenium.webdriver.common.keys import Keys
#from helperIdeaNet import *
import re,pickle
from selenium import webdriver
from process_category import *

# ### overloading BeautifulSoup function

print 'Starting up'

dirname, filename = os.path.split(os.path.abspath(__file__))
os.chdir(dirname)
driver = webdriver.Chrome()
log_dir = os.getcwd()+'/logs'
createDir(log_dir)
logger = Record_Results(log_dir+'/process_topic_board.log')
logger.fprint('Starting..')

# Login
login_ar(driver)

logger.fprint('Collecting categories')
process_category = Process_Category(logger, webdriver=driver, log_dir=log_dir)

categories = process_category.getCategories()

logger.fprint('Found categories',(len(categories)))

process_category.collectCategories(pickle_file_name='cat_topics.pkl')

cat_topics = loadData('cat_topics.pkl', path=log_dir)

process_category.numTopics()

def process_board(board_url):
	print board_url
	driver.get(board_url)
	html = driver.page_source
	soup = Soup(html)
	grid_module = soup.find("div",{"class":"Module User draggable gridItem"})
	print len(grid_module)
	print grid_module




def process_topic_people(people_url):
	print people_url
	driver.get(people_url)
	html = driver.page_source
	soup = Soup(html)


for cat, topics in cat_topics.iteritems():
	print cat, topics
	for topic in topics[:1]:
		topic_string = urllib.quote(topic.decode('utf-8').encode('latin-1'))
		board_url = 'http://www.pinterest.com/search/boards/?q='+topic_string
		#process_topic_board(board_url)
		people_url = 'http://www.pinterest.com/search/people/?q=' + topic_string
		process_topic_people(people_url)

driver.close()


#removeKeys = ['videos','everything','popular','quotes']
#for key in removeKeys:
#    del cat_topics[key]
