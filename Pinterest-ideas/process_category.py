from bs4 import BeautifulSoup
from urllib import urlopen
from utils import *
from selenium.webdriver.common.keys import Keys
#from helperIdeaNet import *
import re,pickle
from selenium import webdriver
from process_category import *

def Soup(item):
  return BeautifulSoup(item,'lxml')

class Process_Category(object):
	def __init__(self, logger, webdriver=None, log_dir=None):
		assert webdriver is not None
		assert  log_dir is not None
		self.log_dir = log_dir
		self.logger = logger
		self.webdriver=webdriver
		pass

	# ### It gets the underscore casing keys for the categories
	def getKey(self, value):
		value = value.lower().replace("'", "")
		items = value.split('and')
		if len(items) ==1:
			items = value.split(' ')
		category = items[0].strip()
		if len(items)>1:
			for item in items[1:]:
				category += "_"+item.strip()
		if "animals" in category:
			category = "animals"
		elif "kids" in category:
			category ="kids"
		elif "music" in category:
			category = "film_music_books"
		return category

	###  It collects and displays top level categories

	def getCategories(self):
		html = urlopen('https://www.pinterest.com/categories/').read()
		soup = Soup(html)
		categoryLinks = soup.select(".categoryLinkWrapper")
		categories = {}
		for categoryLink in categoryLinks:
			category = str(categoryLink.contents[1].contents[0])
			key = self.getKey(category)
			categories[key] = category
			#print key,':',category
		self.categories = categories
		return categories

	def getTopics(self,category):
		url = 'https://www.pinterest.com/categories/' + category
		self.webdriver.get(url)
		html = self.webdriver.page_source
		soup = Soup(html)
		subcategories = soup.find_all("div",{"class": 'interestMaskAndWrapper'})
		topics = []
		for subcategory in subcategories:
			try:
				innercontent = subcategory.contents[1].contents[1]
				innercontentText = \
				str(innercontent).split('{')[1].split("}")[0].split(
					'"interest":')[1]
				topic = re.sub('[^A-Za-z0-9]+', '', innercontentText)
				topics += [topic]
			except Exception:
				print 'exception'
				pass

		return topics

	# ### Checks for new subcategories
	def checkNewTopics(self,category='womens_fashion'):
		topics = []
		topics = self.getTopics(category)
		while True:
			newTopics = self.getTopics(category)
			new = list(set(newTopics) - set(topics))
			if not new:
				return topics
			else:
				topics = list(set(topics + newTopics))

	def cleanCategory(self,innercontent):
		soup = Soup(str(innercontent))
		href = soup.find('a').get('href')
		return href.split('explore/')[1].split("/")[0]

	# ### Extracts related topics

	def getRelatedTopics(self, subcategory):
		url = 'https://www.pinterest.com/explore/' + subcategory
		self.webdriver.get(url)
		html = self.webdriver.page_source
		soup = Soup(html)
		subcategories = soup.find_all("div", {"class": 'interestMaskAndWrapper'})
		topics = []

		for subcategory in subcategories:
			innercontent = subcategory.contents[1]
			topic = self.cleanCategory(innercontent)
			topics += [topic]

		return topics

	# ### Gets subcategories of top level categories
	def collectCategories(self,pickle_file_name='cat_topics.pkl'):
		cat_topics = {}
		for category in self.categories.keys()[:1]:
			self.logger.fprint('\nCategory :',category,'processing...')
			self.logger.fprint('=================================')
			subcategories = self.checkNewTopics(category)

			topics = []
			for subcategory in subcategories:
				topics.append(subcategory)
				self.logger.fprint('Finding related Topics to',subcategory,
				              'processing......')
				relatedTopics = self.getRelatedTopics(subcategory)
				topics.extend(relatedTopics)

			cat_topics[category] = list(set(topics))
		saveData(cat_topics,pickle_file_name, path=self.log_dir)
		self.logger.fprint('saving...cat_topics')
		self.cat_topics = cat_topics
		return cat_topics

	def numTopics(self, unique=False):
		TopicList = []
		for key in self.cat_topics.keys():
			TopicList += self.cat_topics[key]
		self.logger.fprint("Number of topics (non-unique)",len(TopicList))
		self.logger.fprint ("Number of topics (unique)",len(set(TopicList)))
		return len(TopicList),len(set(TopicList))
