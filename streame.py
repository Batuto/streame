#-*-coding:utf8;-*-
#qpy:console
#qpy:2
"""
This is the beta release of StreaMe

version: 0.4.2

@Author: Gurzo
@Date: 2015-03-31
"""

version = '0.4.2'

try:
	import pafy
except:
	import site
	import pafy
import androidhelper
import json
import os
import sys
import re
import time
import urllib
import urllib2

droid = None
downloading = False
dpath = ''


def play(title, stream):
	extrap = {'itemTitle':title}
	try:
		activity = droid.startActivityForResult('android.intent.action.VIEW', 
		                    uri = stream, 
							extras = extrap, 
							type = 'application/mp4', 
							packagename = 'org.videolan.vlc.betav7neon')
		assert activity.error == None
		return True
	except Exception, e:
		print e
		return False

def download(totalbytes, bytesdone, percent, rate, eta):
	global downloading
	if not downloading:
		downloading = True
		droid.dialogCreateHorizontalProgress(title='Downloading on',message=dpath,maximum_progress=100)
		droid.dialogShow()
	else:
		droid.dialogSetCurrentProgress(int(round(percent,2)*100))
		if percent == 1.0:
			downloading = False
			droid.dialogDismiss()
			#droid.notify('StreaMe','Download Complete!')
			droid.makeToast('Download Complete!')

def share(stream):
	droid.setClipboard(stream)
	droid.makeToast('Link copied to clipboard')
	return True

def retrivingStats(message):
	#print message
	#print time.time()
	pass

def open(url):
	droid.dialogCreateSpinnerProgress(title='Retrieving info',message='Please wait',maximum_progress=100)
	droid.dialogShow()
	video = None 
	try:
		video = pafy.new(url,callback=retrivingStats)
	except ssl.SSLError, s:
		droid.dialogDismiss()
		print 'handshake error in retrirving info: ' + str(s.args)
		droid.makeToast('Network error!')
		return False
	except urllib2.URLError, u:
		droid.dialogDismiss()
		print 'url error in retrirving info: ' + str(u.args)
		droid.makeToast('Network error!')
		return False
	except IOError, i:
		droid.dialogDismiss()
		print 'video error in retrirving info: ' + str(i.args)
		droid.makeToast('Youtube says: This video is unavailable!')
		return False
	except Exception, e:
		droid.dialogDismiss()
		print 'some error in retrirving info: ' + str(e.args)
		return False

	droid.dialogDismiss()
	
	audiostreams = video.audiostreams
	audioquality = [a.bitrate + ' - ' + '%.2f' % round((float(a.get_filesize()) / 1024 )/ 1024, 2) + 'MB' for a in audiostreams]
	title = str(video.title)
	action = choose('Select action', ['Stream','Download','Copy URL'], no = 'Cancel')
	if action == 0:
		choice = choose('Select audio quality', audioquality, no = 'Cancel')
		if choice == 'negative' or choice == 'c':
			return False
		stream = audiostreams[choice].url
		return play(title, stream)
	elif action == 1:
		choice = choose('Select audio quality', audioquality, no = 'Cancel')
		if choice == 'negative' or choice == 'c':
			return False
		result = audiostreams[choice].download(filepath=dpath, quiet=True, callback=download)
		return True
	elif action == 2:
		return share(url)
	else:
		return False

def searchYT(word, page):
	droid.dialogCreateSpinnerProgress(title='Searching',message='Please wait',maximum_progress=100)
	droid.dialogShow()
	param = { 'q' : word, 'sm' : '3', 'filters' : 'video', 'lclk' : 'video', 'page' : page}
	query = urllib.urlencode(param)
	url = 'https://www.youtube.com/results?' + query
	
	htmlSource = ''
	try:
		conn = urllib2.urlopen(url, timeout=5)
		htmlSource = conn.read()
	except urllib2.URLError, u:
		droid.dialogDismiss()
		print 'network error in searching: ' + str(u.args)
		droid.makeToast('Network error!')
		return 'error'
	except Exception, e:
		droid.dialogDismiss()
		if e == '<urlopen error timed out>':
			print 'Time out error in searching:' + str(e.args)
			droid.makeToast('Connection timedout!')
			return 'timeout'
		return 'error'
	
	#droid.dialogDismiss()
	#droid.dialogCreateSpinnerProgress(title='Analyzing',message='Please wait',maximum_progress=100)
	#droid.dialogShow()
	
	search_results = re.findall(r'href=\"\/watch\?v=(.{11})', htmlSource)
	urls = ['http://www.youtube.com/watch?v=' + id for id in search_results[0:][::2]]
	titles = re.findall('title=\"([^"]{5,})\" rel="spf-prefetch" aria-describedby', htmlSource)
	if len(titles) == 0:
		titles = re.findall('title=\"([^"]{5,})\" aria-describedby', htmlSource)
	
	droid.dialogDismiss()
	return (titles, urls)
	
def search(by = '', page = 1):	
	word = ''
	if page == 1:
		line = droid.dialogGetInput(title='YouTube', message='Search for')
		if line.result == None or line.result == 'negative':
			return
		elif line.result == '':
			droid.makeToast('You must insert something!')
			return search()
		word = line.result
	else:
		word = by
	
	result  = searchYT(word, page)
	if result == 'timeout':
		return False
	elif result == 'error':
		return False
	
	played = False
	while True:
		choice = choose('Search result on page ' + str(page), result[0], no='Cancel', yes='Next page')
		if choice == 'negative':
			return search()
		elif choice == 'positive':
			search(word, page+1)
		elif choice < len(result[1]):
			played = open(result[1][choice])
		else:
			break
	
	return played

def insert():
	line = droid.dialogGetInput(title='StreaMe', message='Insert URL')
	if line.result == '':
		droid.makeToast('You must insert a URL!')
		return insert()
	elif line.result != None:
		url = line.result
		played = open(url)
		if not played:
			return insert()
		return True
	return False
	
def choose(title, flist, no = 0, yes = 0):
	droid.dialogCreateAlert(title, '')
	droid.dialogSetItems(flist)
	if yes:
		droid.dialogSetPositiveButtonText(yes)
	if no:
		droid.dialogSetNegativeButtonText(no)
	droid.dialogShow()
	resp = droid.dialogGetResponse()
	droid.dialogDismiss()
	s = 0
	if resp.result.has_key('item'):
		return resp.result['item']
	if resp.result.has_key('which'):
		return resp.result['which']
	elif resp.result.has_key("canceled"):
		return 'c'
	return resp.result

def update():
	droid.makeToast('Download update')
	os.remove(sys.argv[0])
	url = 'https://raw.githubusercontent.com/Gurzo/streame/master/streame.py'
	conn = urllib2.urlopen(url)
	html = response.read()
	file = open('streame.py', 'w')
	file.write(html)
	file.close()
	exit(0)

def checkUpdate():
	url = 'https://raw.githubusercontent.com/Gurzo/streame/master/version.txt'
	conn = urllib2.urlopen(url)
	file = conn.read()
	if not version == str(file):
		droid.makeToast('New version avaible')
		return True
	return False
	
def setDownloadPath():
	global dpath
	env = droid.environment()
	if env.result.has_key('download'):
		dpath = env.result['download'] + '/'
	else:
		folders = os.environ
		if folders.has_key('EXTERNAL_STORAGE'):
			dpath = folders['EXTERNAL_STORAGE'] + '/Download/'
		elif folders.has_key('SECONDARY_STORAGE'):
			dpath = folders['SECONDARY_STORAGE'] + '/'
		elif folders.has_key('ANDROID_PUBLIC'):
			dpath = folders['ANDROID_PUBLIC'] + '/'
	return

def createDroid():
	for i in range(3):
		try:
			global droid
			droid = androidhelper.Android()
			return
		except:
			pass
	print 'Error encurred during init operation \n Please restart application.'
	print 'If the problem persist \n Try kill and reopen QPython interpreter'
	print 'Finally, please restart your device'
	quit()

def welcome():
	message = []
	message.append('')
	message.append('##### ##### ####  ##### ##### #   # #####' )
	message.append('#       #   #   # #     #   # ## ## #    ' )
	message.append('#####   #   ####  ##### ##### # # # #####' )
	message.append('    #   #   # #   #     #   # #   # #    ' )
	message.append('#####   #   #  #  ##### #   # #   # #####' )
	message.append('')
	message.append('/' + '+' * 39 + '\\' )
	message.append('#' + ' ' * 39 + '#' )
	message.append('#  This is the beta release of StreaMe  #')
	message.append('#   @Version: ' + version + '                     #' )
	message.append('#   @Author: Gurzo                      #' )
	message.append('#   @Date: 2015-03-31                   #' )
	message.append('#' + ' ' * 39 + '#' )
	message.append('\\' + '+'  * 39 + '/' )
	message.append('')
	message.append('To resume last page, press back and Ok')
	message.append('')
	for line in message:
		print line

def quit():
	print 'Program terminated, please'
	exit(0)

def main():
	welcome()
	createDroid()
	setDownloadPath()
	if checkUpdate():
		update()
	while 1:
		title = 'Welcome to StreaMe'
		flist = ['Search on YouTube', 'Insert URL']
		action = choose(title, flist, no = 'Exit')
		if action == 1:
			insert()
		elif action == 0:
			search()
		elif action == 'negative':
			quit()
		elif action == 'c':
			quit()

if __name__ == '__main__':
	main()
