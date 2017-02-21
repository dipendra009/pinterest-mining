import subprocess, shlex, time
import numpy as np
import time, json, hashlib
import sys, os, datetime
import re,pickle
from selenium.webdriver.common.keys import Keys


class Record_Results(object):
	def __init__(self, logfile):
		if '.' not in logfile:
			logfile = logfile + '.log'
		# print 'logfile::::', logfile
		if os.path.isfile(logfile):
			vi = 0
			while os.path.exists(logfile):
				#print 'Log file exists: ', logfile
				ext = logfile.split('.')[-1]
				filename = logfile[:-len(ext) - 1]
				# print '1:',filename
				file_suff = filename.split('_')[-1]
				# print '2:', file_suff
				filename = filename[:-len(file_suff) - 1]
				# print '3:', filename
				vi += 1
				try:
					if 'v' in file_suff:
						file_suff = 'v' + str(vi)
					# print 'filesuff', file_suff
					else:
						file_suff = file_suff + '_v' + str(vi)
				except:
					file_suff += get_date_str()
				# print 'filename:',filename, 'fil_suff', file_suff, 'ext:', ext
				logfile = filename + '_' + file_suff + '.' + ext
		self.logfile = logfile
		print 'Using logfile: ', logfile
		# print 'logfile:', logfile
		self.f = open(logfile, 'w')
		self.close()

	def fprint(self, *stt):
		sto = reduce(lambda x, y: str(x) + ' ' + str(y), list(stt))
		print sto
		try:
			self.open()
			self.f.write('\n' + str(datetime.datetime.now()) + ':' + sto)
			# print 'wrote...', sto, 'to file'
			self.close()
		except:
			pass

	def open(self):
		self.f = open(self.logfile, 'a')

	def fcopy(self, filename):
		self.open()
		str = open(filename, 'r').read()
		self.f.write('\n' + str)
		self.close()

	def close(self):
		try:
			self.f.close()
		except:
			pass


# ### Function for loading and saving the dictionary as a pickle
def loadData(name, path="."):
	'''
	This loads a pickle file and returns the content which is a DICTIONARY object in our case.
	'''
	if ".pkl" in name:
		name = name.split(".pkl")[0]
	if "/" in name:
		name = name.split("/", 1)[1]

	with open(path + "/" + name + '.pkl', 'rb') as f:
		return pickle.load(f)


def saveData(obj, name, path="."):
	'''
	This saves a object into a pickle file. In our case, it is generally a DICTIONARY object.
	'''
	if '.pkl' not in name: name += '.pkl'
	with open(path + "/" + name, 'wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def get_md5(data):
	return hashlib.md5(json.dumps(data, sort_keys=True)).hexdigest()


def get_date_str():
	datetim = str(datetime.datetime.now()).replace('.', '').replace('-',
	                                                                '').replace(
		':', '').replace(' ', '')[2:14]
	return datetim


def createDir(direc):
	command = "mkdir -p " + direc
	# print "create dir for ", direc
	if not (os.path.exists(direc) and os.path.isdir(direc)):
		os.system(command)


def run_command(args, timeout=100000):
	print "Command: ", args
	args = shlex.split(args)
	p = subprocess.Popen(args,
	                     stdout=subprocess.PIPE)  # , stdin=None, stdout=PIPE, stderr=None)
	op = ""
	if timeout == 0:
		timeout = 1
	pid = p.pid
	time.sleep(1)
	for i in range(timeout):
		if p.poll() is 0:
			op, err = p.communicate(None)
			return op, pid
		else:
			time.sleep(10)
	if p.poll() is not 0:
		p.kill()
		print "Timeout, killed process"
	else:
		op, err = p.communicate(None)
	return op, pid

def login_ar(driver):
	# ### Login in Pinterest

	driver.get('https://www.pinterest.com/login')
	email = driver.find_element_by_name('username_or_email')
	email.send_keys('swanson8813@gmail.com')
	password = driver.find_element_by_name('password')
	password.send_keys('ideanet' + Keys.RETURN)
