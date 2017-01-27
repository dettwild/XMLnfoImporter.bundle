#########################################
# XMLnfoImporter  Agent (secondary)
#########################################
#
# spec'd from: http://kodi.wiki/view/Import_-_Export_Library#Video_nfo_Files
#
# modified by dd to include ONLY XML metadata
#
# Original code author: Harley Hooligan
# Modified by Guillaume Boudreau
# Eden and Frodo compatibility added by Jorge Amigo
# Cleanup and some extensions by SlrG
# Multipart filter idea by diamondsw
# Logo by CrazyRabbit
#
#
#
#

import os, re, time, datetime, platform, traceback, re, htmlentitydefs #, glob
from dateutil.parser import parse

import urllib2
#from common import *
#import requests   #needed for HTML request to set watched state

COUNTRY_CODES = {
  'Australia': 'Australia,AU',
  'Canada': 'Canada,CA',
  'France': 'France,FR',
  'Germany': 'Germany,DE',
  'Netherlands': 'Netherlands,NL',
  'United Kingdom': 'UK,GB',
  'United States': 'USA,',
}

PERCENT_RATINGS = {
  'rottentomatoes','rotten tomatoes','rt','flixster'
}



### general function outside a class (hope this works)
def DLog (LogMessage):
	if Prefs['debug']:
		Log (LogMessage)




###### function to remove empty tags from a XML structure -- used to 'clean up'
def RemoveEmptyTags(xmltags):
	for xmltag in xmltags.iter("*"):
		if len(xmltag):
			continue
		if not (xmltag.text and xmltag.text.strip()):
			DLog("Removing empty XMLTag: " + xmltag.tag + " in  - " + xmltag.getparent().tag)
			xmltag.getparent().remove(xmltag)
	return xmltags


	##
	# Removes HTML or XML character references and entities from a text string.
	# Copyright: http://effbot.org/zone/re-sub.htm October 28, 2006 | Fredrik Lundh
	# @param text The HTML (or XML) source text.
	# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return unichr(int(text[3:-1], 16))
				else:
					return unichr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text # leave as is
	return re.sub("&#?\w+;", fixup, text)









class xmlnfo(Agent.Movies):
	name = 'XML nfo Importer (Movies)'
	ver = '0.01'
	primary_provider = False
	languages = [Locale.Language.NoLanguage]
	contributes_to = ['com.plexapp.agents.imdb', #Plex Movie Agent
					  'com.plexapp.agents.themoviedb',  #The Movie Database Agent
					  'com.plexapp.agents.none',  #Personal Media Agent
					  'com.plexapp.agents.data18']


	def getRelatedFile(self, videoFile, fileExtension):
		videoFileExtension = videoFile.split(".")[-1]
		videoFileBase = videoFile.replace('.' + videoFileExtension, '')
		videoFileBase = re.sub(r'(?is)\s*\-\s*(cd|dvd|disc|disk|part|pt|d)\s*[0-9]$', '', videoFileBase)
		videoFileBase = re.sub(r'(?is)\s*\-\s*(cd|dvd|disc|disk|part|pt|d)\s*[a-d]$', '', videoFileBase)
		return (videoFileBase + fileExtension)

	def getMovieNameFromFolder(self, folderpath, withYear):
		foldersplit = folderpath.split (os.sep)
		if withYear == True:
			if foldersplit[-1] == 'VIDEO_TS':
				moviename = os.sep.join(foldersplit[1:len(foldersplit)-1:]) + os.sep + foldersplit[-2]
			else:
				moviename = os.sep.join(foldersplit) + os.sep + foldersplit[-1]
			DLog("Moviename from folder (withYear): " + moviename)
		else:
			if foldersplit[-1] == 'VIDEO_TS':
				moviename = os.sep.join(foldersplit[1:len(foldersplit)-1:]) + os.sep + re.sub (r' \(.*\)',r'',foldersplit[-2])
			else:
				moviename = os.sep.join(foldersplit) + os.sep + re.sub (r' \(.*\)',r'',foldersplit[-1])
			DLog("Moviename from folder: " + moviename)
		return moviename


	def time_convert (self, duration):
		if (duration <= 2):
			duration = duration * 60 * 60 * 1000 #h to ms
		elif (duration <= 120):
			duration = duration * 60 * 1000 #m to ms
		elif (duration <= 7200):
			duration = duration * 1000 #s to ms
		return duration

	
	def checkFilePaths(self, pathfns, ftype):
		for pathfn in pathfns:
			DLog("Trying " + pathfn)
			if not os.path.exists(pathfn):
				continue
			else:
				Log("Found " + ftype + " file " + pathfn)
				return pathfn
		else:
			Log("No " + ftype + " file found! Aborting!")


	def FloatRound(self, x):
		return x + 0.5 / 2 - ((x + 0.5 / 2) % 0.5)



##### search function #####
	def search(self, results, media, lang):
		DLog("++++++++++++++++++++++++")
		DLog("Entering search function")
		DLog("++++++++++++++++++++++++")
		Log("" + self.name + " Version: " + self.ver)

		Log("Langage in search fct is : " + lang)
		try: Log("Media primary_metadata Variable is : " + str(media.primary_metadata))
		except:
			Log("Was not able to Log media.primary_metadata")
			pass
		try: Log("Media primary_agent Variable is : " + str(media.primary_agent))
		except:
			Log("Was not able to Log media.primary_agent")
			pass
		try: Log("Media filename Variable is : " + str(media.filename))
		except:
			Log("Was not able to Log media.filename")
			pass
		try: Log("Media ID Variable is : " + str(media.id))
		except:
			Log("Was not able to Log media.id")
			pass
		try: Log("Media GUID Variable is : " + str(media.guid))
		except:
			Log("Was not able to Log media.guid")
			pass
		try: Log("Media Name Variable is : " + media.name)
		except:
			Log("Was not able to Log media.name")
			pass
		try: Log("Media Year Variable is : " + str(media.year))
		except:
			Log("Was not able to Log media.year")
			pass
		try: Log("Media duration Variable is : " + str(media.duration))
		except:
			Log("Was not able to Log media.duration")
			pass
		try: Log("Media GUID Variable is : " + str(media.guid))
		except:
			Log("Was not able to Log media.guid")
			pass

		results.Append(MetadataSearchResult(id = 'null', score = 100))    #copied from localmedia agent - hoping that a SECONDARY Agent is ok to only do UPDATE




##### update Function #####
	def update(self, metadata, media, lang):
		DLog("++++++++++++++++++++++++")
		DLog("Entering update function")
		DLog("++++++++++++++++++++++++")
		Log ("" + self.name + " Version: " + self.ver)
		
		Log("Langage in search fct is : " + lang)
		try: Log("Media primary_metadata Variable is : " + str(media.primary_metadata))
		except:
			Log("Was not able to Log media.primary_metadata")
			pass
		try: Log("Media primary_agent Variable is : " + str(media.primary_agent))
		except:
			Log("Was not able to Log media.primary_agent")
			pass
		try: Log("Media filename Variable is : " + str(media.filename))
		except:
			Log("Was not able to Log media.filename")
			pass
		try: Log("Media ID Variable is : " + str(media.id))
		except:
			Log("Was not able to Log media.id")
			pass
		try: Log("Media GUID Variable is : " + str(media.guid))
		except:
			Log("Was not able to Log media.guid")
			pass
		try: Log("Media Name Variable is : " + media.name)
		except:
			Log("Was not able to Log media.name")
			pass
		try: Log("Media Year Variable is : " + str(media.year))
		except:
			Log("Was not able to Log media.year")
			pass
		try: Log("Media duration Variable is : " + str(media.duration))
		except:
			Log("Was not able to Log media.duration")
			pass
		try: Log("Media GUID Variable is : " + str(media.guid))
		except:
			Log("Was not able to Log media.guid")
			pass
		Log("loging ALL of 'media' and 'metadata' below")
		#Log(media.items)
		Log(media.items[0])
		#Log(media.items[1])
		#Log(media.items[2])
		#for mymediaitem in media.count():
		#	Log(media[mymediatiem])
			
		#Log(metadata.items[0])
		#Log(metadata.items[1])
		#Log(metadata.items[2])
		#####################################read full XML of an iten and extract value for tag 'viewCount'
		#Log(metadata.viewCount)



		parse_date = lambda s: Datetime.ParseDate(s).date()
		path1 = media.items[0].parts[0].file
		DLog('media file: ' + path1)
		folderpath = os.path.dirname(path1)
		DLog('folderpath: ' + folderpath)
		isDVD = os.path.basename(folderpath).upper() == 'VIDEO_TS'
		if isDVD: folderpathDVD = os.path.dirname(folderpath)

		# Moviename with year from folder
		movienamewithyear = self.getMovieNameFromFolder (folderpath, True)
		# Moviename from folder
		moviename = self.getMovieNameFromFolder (folderpath, False)

		
		nfoNames = []       #initialize array to empty
		# Eden / Frodo
		nfoNames.append (self.getRelatedFile(path1, '.nfo'))
		nfoNames.append (movienamewithyear + '.nfo')
		nfoNames.append (moviename + '.nfo')
		# movie.nfo (e.g. FilmInfo!Organizer users)
		nfoNames.append (os.path.join(folderpath, 'movie.nfo'))
		# last resort - use first found .nfo
		nfoFiles = [f for f in os.listdir(folderpath) if f.endswith('.nfo')]
		if nfoFiles: nfoNames.append (os.path.join(folderpath, nfoFiles[0]))

		# check possible .nfo file locations
		nfoFile = self.checkFilePaths (nfoNames, '.nfo')

		if nfoFile:
			nfoText = Core.storage.load(nfoFile)
			nfoText = re.sub(r'&(?![A-Za-z]+[0-9]*;|#[0-9]+;|#x[0-9a-fA-F]+;)', r'&amp;', nfoText)
			nfoTextLower = nfoText.lower()
			if nfoTextLower.count('<movie') > 0 and nfoTextLower.count('</movie>') > 0:    #contains the main tags --> lools like a KODI nfo file
				
				# Remove URLs (or other stuff) at the end of the XML file
				nfoText = '%s</movie>' % nfoText.rsplit('</movie>', 1)[0]   #diff between rspit and split?

				# likely an xbmc nfo file
				#Log(nfoText)
				try: nfoXML = XML.ElementFromString(nfoText).xpath('//movie')[0]
				except:
					DLog('ERROR: Cant parse XML in nfo-file : ' + nfoFile + '. Aborting!')
					return
				Log(nfoXML[0])   #logs FIRST element, as elemeent, content with .text method - named el with .xpath("name")

				#remove empty xml tags
				DLog('Removing empty XML tags from movies nfo...')
				nfoXML = RemoveEmptyTags(nfoXML)

				### NOW actually extracting the information from the XML field by field:
				
				## experimenta lsection to set WATCHED state (only if true, NOT setting sth to unwatched if XML in nfo indicates that)
				#trying to GET xml of item in order to read viewCount tag
				myurl = "http://192.168.66.2:32400/library/metadata/11976?X-Plex-Token=tbcdQx1Q71KHnN3fCYaH"
				myans = HTTP.Request(myurl)
				#Log(myans)
				#try: 
				#	ansxml = XML.ElementFromString(myans).xpath('//MediaContainer')[0]
				#	Log(ansxml)
				#except:
				#	DLog("Cant parse movie XML")
				#	pass
				try:
					myviewcount = XML.ElementFromString(myans).xpath('//MediaContainer/Video/@viewCount')[0]
				except:
					myviewcount = 0
				Log("the obtained watch count is : " + str(myviewcount))
				#Log(ansxml.xpath("Video")[0])
				#Log(ansxml.xpath('//MediaContainer/Video/@viewCount')[0])
				#Log(ansxml.xpath("Video")[0].text)
				#Log(ansxml.xpath("Video/@viewCount")[0])
				Log("did above work?")
				#Log(ansxml.xpath("Video")[0][0])
				#Log(ansxml.xpath("Video")[0][1].text)
				#Log(ansxml.xpath("Video")[0].xpath("viewCount")[0].text)
				#ans0 = HTTP.Request("http://localhost:32400/:/timeline?X-Plex-Token=tbcdQx1Q71KHnN3fCYaH&identifier=com.plexapp.plugins.library&key=" + media.id)
				#Log(ans0)
				#ans1 = HTTP.Request("http://localhost:32400/myplex/account?X-Plex-Token=tbcdQx1Q71KHnN3fCYaH")
				#Log(ans1)
				try: 
					#my.plexapp.com/pms/system/library/sections
					ans1 = HTTP.Request("http://localhost:32400/myplex/account")
					Log(ans1)
				except:
					Log("issue with web request or logging of answer")
					pass
				
				myserver = "127.0.0.1"
				mycommandstr = "http://<pms server>:32400/:/scrobble?key=554&identifier=com.plexapp.plugins.library"
				myauth_token = "tbcdQx1Q71KHnN3fCYaH"
				# http://dd-ros6:32400/web/index.html#
				# http://192.168.66.2:32400/:/scrobble?key=11976&identifier=com.plexapp.plugins.library
				# Request: [192.168.66.4:61826 (Subnet)] GET /:/scrobble?identifier=com.plexapp.plugins.library&key=11976
				# X-Plex-Token => tbcdQx1Q71KHnN3fCYaH
				# http://192.168.66.2:32400/:/unscrobble?key=11976&identifier=com.plexapp.plugins.library&X-Plex-Token=tbcdQx1Q71KHnN3fCYaH
				mycommand ="http://192.168.66.2:32400/:/scrobble?key=11976&identifier=com.plexapp.plugins.library&X-Plex-Token=tbcdQx1Q71KHnN3fCYaH"
				myurl = "http://192.168.66.2:32400/:/scrobble"
				myurl2 = "http://192.168.66.2:32400/:/scrobble?key=11976&identifier=com.plexapp.plugins.library"
				mytoken1 = "tbcdQx1Q71KHnN3fCYaH"
				mytoken = "QBuAHqWHPpaxefxxsoSq"
				myurl3 = "http://192.168.66.2:32400/:/scrobble?identifier=com.plexapp.plugins.library&key=" + media.id + "&X-Plex-Token=" + mytoken
				Log(myurl3)
				#Log("command = " + mycommand)
				#myvalues2 = {"X-Plex-Token":mytoken}
				#Log(myvalues2)
				try: 
					myvalues = {"key":11976, "identifier": "com.plexapp.plugins.library","X-Plex-Token":mytoken}
					#Log(myvalues)
				except:
					Log("unable to set dict myvalues")
					pass
				mypluginid = Plugin.Identifier  #returns com.plexapp.agents.xmlnfo
				Log(mypluginid)
				Log("Server platform OS / CPU : " + Platform.OS + " / " + Platform.CPU)
				#Log("Client platform & Protocols : " + str(Client.Platform) + " / " + str(Client.Protocols))
				Log("Server IP, publ IP and hostname are : " + str(Network.Address) + " / " + str(Network.PublicAddress) + " / " + str(Network.Hostname))
				Log("===============================================================")
				#myreply = HTTP.Request(mycommand)
				#myans = HTTP.Request(myurl,myvalues, cacheTime=0)
				#Log(myans)
				try:
					#myreply = HTTP.Request(mycommand)
					myreply = HTTP.Request(myurl3,sleep=0.3) #,myvalues2) #, cacheTime=0)
					#myreply = request.get(mycommand)
					#GET(mycommand)
					#subprocess.call("curl","-X","GET",mycommand)
					#f = urllib2.urlopen(mycommand)
					#for x in f:
					#	Log(x)
					#f.close()
				except:
					Log("WEB request failed!!")
					pass
				try:
					Log("the reply is:")
					Log(myreply)
				except: 
					Log("Logging of web-answer failed!")
					pass
				
				#=========   TITLE   =========     --edited (made 3 lines out of one with temp var mytitle to improve LOG and test coding
				Log("======= TITLE ========")
				#####tst1 = XML.StringFromElement(
				myval = None
				try:
					myval= nfoXML.xpath('title')[0].text    #.strip()
					Log("Value for <title> in nfo-file is :" + myval)
				except:
					Log("No <title> tag in nfo-file : " + nfoFile)
					pass
				if myval:
					try:
						metadata.title = myval
						Log("Plex item 'metadata.title' was just set to : " + metadata.title)
					except:
						Log("UNABLE to assing <title> to Plex item 'metadata.title'!")
						pass
								
				#=========   ORIGINALTITLE   ========= 
				DLog("======= ORIGINALTITLE ========")
				myval = None
				try:
					myval = nfoXML.xpath('originaltitle')[0].text   #.strip()
					Log("Value for <originaltitle> in nfo-file is :" + myval)
				except:
					Log("No <originaltitle> tag in nfo-file : " + nfoFile)
					pass
				if myval:
					try:
						metadata.original_title = myval
						Log("Plex item 'metadata.original_title' was just set to : " + metadata.original_title)
					except:
						Log("UNABLE to assing <originaltitle> to Plex item 'metadata.original_title'!")
						pass
				

				#=========   SORTTITLE   ========= 
				DLog("======= SORTTITLE ========")
				myval = None
				try: DLog("Current 'metadata.title_sort' is : " + metadata.title_sort)    #remove later
				except: pass                                                              #remove later
				try: 
					myval = nfoXML.xpath('sorttitle')[0].text   #.strip()
					DLog("Value for <sorttitle> in nfo-file is : " + myval)
				except: 
					DLog("No <sorttitle> tag in nfo-file : " + nfoFile)
					pass
				if myval:
					try:
						metadata.title_sort = myval
						DLog("Plex item 'metadata.title_sort' was just set to : " + metadata.title_sort)
					except:
						DLog("UNABLE to assign <sorttitle> to Plex item 'metadata.title_sort'!")

				#=========   YEAR   ========= 
				DLog("======= YEAR ========")
				myval = None				
				try: metadata.year = int(nfoXML.xpath("year")[0].text.strip())
				except: pass
					
				
				# Content Rating
				metadata.content_rating = ''
				content_rating = {}
				mpaa_rating = ''
				try:
					mpaatext = nfoXML.xpath('./mpaa')[0].text.strip()
					match = re.match(r'(?:Rated\s)?(?P<mpaa>[A-z0-9-+/.]+(?:\s[0-9]+[A-z]?)?)?', mpaatext)
					if match.group('mpaa'):
						mpaa_rating = match.group('mpaa')
						DLog('MPAA Rating: ' + mpaa_rating)
				except: pass
				try:
					for cert in nfoXML.xpath('certification')[0].text.split(" / "):
						country = cert.strip()
						country = country.split(':')
						if not country[0] in content_rating:
							if country[0] == "Australia":
								if country[1] == "MA": country[1] = "MA15"
								if country[1] == "R": country[1] = "R18"
								if country[1] == "X": country[1] = "X18"
							content_rating[country[0]]=country[1].strip('+')
					DLog('Content Rating(s): ' + str(content_rating))
				except: pass
				if Prefs['country'] != '':
					cc = COUNTRY_CODES[Prefs['country']].split(',')
					DLog('Country code from settings: ' + Prefs['country'] + ':' + str(cc))
					if cc[0] in content_rating:
						if cc[1] == "":
							metadata.content_rating = content_rating.get(cc[0])
						else:
							metadata.content_rating = '%s/%s' % (cc[1].lower(), content_rating.get(cc[0]))
				if metadata.content_rating == '' and mpaa_rating != '':
					metadata.content_rating = mpaa_rating
				if metadata.content_rating == '' and 'USA' in content_rating:
					metadata.content_rating = content_rating.get('USA')
				if metadata.content_rating == '':
					metadata.content_rating = 'NR'

				##### Studio
				try: metadata.studio = nfoXML.xpath("studio")[0].text.strip()
				except: pass
				
				##### Premiere / Release Date
				try:
					release_string = None
					try:
						DLog("Reading releasedate tag...")
						release_string = nfoXML.xpath("releasedate")[0].text.strip()
						DLog("Releasedate tag is: " + release_string)
					except:
						DLog("No releasedate tag found...")
						pass
					if not release_string:
						try:
							DLog("Reading premiered tag...")
							release_string = nfoXML.xpath("premiered")[0].text.strip()
							DLog("Premiered tag is: " + release_string)
						except:
							DLog("No premiered tag found...")
							pass
					if not release_string:
						try:
							DLog("Reading dateadded tag...")
							release_string = nfoXML.xpath("dateadded")[0].text.strip()
							DLog("Dateadded tag is: " + release_string)
						except:
							DLog("No dateadded tag found...")
							pass
					if release_string:
						if not Prefs['correctdate']:
							release_date = parse_date(release_string)
						else:
							DLog("Apply date correction: " + Prefs['datestring'])
							if '*' in Prefs['datestring']:
								for char in ['/','-','.']:
									try:
										release_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(release_string, Prefs['datestring'].replace('*', char)))).date()
										self.DLog("Match found: " + Prefs['datestring'].replace('*', char))
									except: pass
							else:
								release_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(release_string, Prefs['datestring']))).date()
				except:
					DLog("Exception parsing releasedate: " + traceback.format_exc())
					pass
				try:
					if not release_date:
						DLog("Fallback to year tag instead...")
						release_date = time.strptime(str(metadata.year) + "-01-01", "%Y-%m-%d")
						metadata.originally_available_at = datetime.datetime.fromtimestamp(time.mktime(release_date)).date()
					else:
						DLog("Setting releasedate...")
						metadata.originally_available_at = release_date
				except: pass

				
				##### Tagline
				try: Log("Tagline BEFORE setting is : " + metadata.tagline)
				except: 
					Log("was not able to log the OLD metadata.tagline field")
					pass

				try: metadata.tagline = nfoXML.xpath("tagline")[0].text.strip()
				except: pass
				try: Log("Tagline str is : " + str(metadata.tagline))
				except: 
					Log("was not able to log the STR metadata.tagline field")
					pass
				try: Log("Tagline raw is : " + metadata.tagline)
				except: 
					Log("was not able to log the RAW metadata.tagline field")
					pass
				
				# Summary (Outline/Plot)
				try:
					if Prefs['plot']:
						DLog("User setting forces plot before outline...")
						stype1 = 'plot'
						stype2 = 'outline'
					else:
						DLog("Default setting forces outline before plot...")
						stype1 ='outline'
						stype2 = 'plot'
					try:
						summary = nfoXML.xpath(stype1)[0].text.strip('| \t\r\n')
						if not summary:
							self.DLog("No or empty " + stype1 + " tag. Fallback to " + stype2 +"...")
							raise
					except:
						summary = nfoXML.xpath(stype2)[0].text.strip('| \t\r\n')
					metadata.summary = summary
				except:
					DLog("Exception on reading summary!")
					pass
				
				try: Dlog("Summary is : " + metadata.summary)
				except: pass
				
				# Ratings
				try:
					nforating = float(nfoXML.xpath("rating")[0].text.replace(',', '.'))
					if Prefs['fround']:
						rating = self.FloatRound(nforating)
					else:
						rating = nforating
					if Prefs['altratings']:
						DLog("Searching for additional Ratings...")
						allowedratings = Prefs['ratings']
						if not allowedratings: allowedratings = ""
						addratingsstring = ""
						addratings = nfoXML.xpath('ratings')
						if addratings:
							for addratingXML in addratings:
								for addrating in addratingXML:
									ratingprovider = str(addrating.attrib['moviedb'])
									ratingvalue = str(addrating.text.replace (',','.'))
									if ratingprovider.lower() in PERCENT_RATINGS:
										ratingvalue = ratingvalue + "%"
									if ratingprovider in allowedratings or allowedratings == "":
										DLog("adding rating: " + ratingprovider + ": " + ratingvalue)
										addratingsstring = addratingsstring + " | " + ratingprovider + ": " + ratingvalue
							DLog("Putting additional ratings at the " + Prefs['ratingspos'] + " of the summary!")
							if Prefs['ratingspos'] == "front":
								if Prefs['preserverating']:
									metadata.summary = addratingsstring[3:] + unescape(" &#9733;\n\n") + metadata.summary
								else:
									metadata.summary = unescape("&#9733; ") + addratingsstring[3:] + unescape(" &#9733;\n\n") + metadata.summary
							else:
								metadata.summary = metadata.summary + unescape("\n\n&#9733; ") + addratingsstring[3:] + unescape(" &#9733;")
					if Prefs['preserverating']:
						DLog("Putting .nfo rating in front of summary!")
						metadata.summary = unescape(str(Prefs['beforerating'])) + "{:.1f}".format(nforating) + unescape(str(Prefs['afterrating'])) + metadata.summary
						metadata.rating = rating
					else:
						metadata.rating = rating
				except:
					DLog("Exception parsing ratings: " + traceback.format_exc())
					pass
				
				try: Log("Rating is : " + str(metadata.rating))
				except: 
					Log("was not able to log the metadata.rating field")
					pass				

				# Writers (Credits)
				# # try:
					# # credits = nfoXML.xpath('credits')
					# # metadata.writers.clear()
					# # [metadata.writers.add(c.strip()) for creditXML in credits for c in creditXML.text.split("/")]
					# # metadata.writers.discard('')
				# # except: pass

				##### trying my own more transparent Writers lookup  ---- WRITERS has a substructure in Plex similar to Role
				Log("now attempting my own WRITERS lookup")
				metadata.writers.clear()
				try: Log("first writer before loop is : " + nfoXML.xpath('credits')[0].text)
				except: pass
				for mywriter in nfoXML.xpath('credits'):
					try: Log("my current Credit/Writer TEXT (not XML) is : " + str(mywriter.text))
					except: 
						Log("Unable to log current TEXT writer")
						pass
					writers = metadata.writers.new()                          ####this creates a NEW object in Plex - the ADD method only works for simple stuff like tags
					writerstring = mywriter.text #.split("/") #[0]      #worked with the [0] at end
					Log("my current Writer-STR is : " + str(writerstring))
					try: 
						writers.name = writerstring
						Log("assigned Writerstring to writers.name")
					except: 
						Log("Unable to assign Writer to Metadata")
						pass


				
				###### Directors  -------------------------------------------------------------------
				try:
					directors = nfoXML.xpath('director')
					metadata.directors.clear()
					[metadata.directors.add(d.strip()) for directorXML in directors for d in directorXML.text.split("/")]
					metadata.directors.discard('')
				except: pass
				

				###### Genres  ------------------------------------------------------------------
				#try:
				#	genres = nfoXML.xpath('genre')
				#	Log("current genre is set to : " + genres)
				#	metadata.genres.clear()     
				#	[metadata.genres.add(g.strip()) for genreXML in genres for g in genreXML.text.split("/")]
				#	metadata.genres.discard('')
				#except: pass

				##### trying my own more transparent GENRE lookup:
				Log("now attempting my own genre lookup")
				metadata.genres.clear()
				for mygenre in nfoXML.xpath('genre'):
					Log("my current genre is : " + str(mygenre))
					#genre = metadata.genres.new()   #NEW is not supported for genres, only for Writers and Roles
					#genrestring = mygenre[0].text.strip()
					genrestring = mygenre.text.split("/")[0]   # .strip()
					#Log("my current genre-LIST is : " + str(genrestring))
					Log("my current genre-STR is : " + genrestring)

					try: metadata.genres.add(genrestring)
					##try: genre = mygenre
					except: pass
#release_string =     nfoXML.xpath("releasedate")[0].text.strip()
#myyear_int =     int(nfoXML.xpath("year")[0].text.strip())
#myorigtitlestring =  nfoXML.xpath('originaltitle')[0].text.strip()


				# Countries
				try:
					countries = nfoXML.xpath('country')
					metadata.countries.clear()
					[metadata.countries.add(c.strip()) for countryXML in countries for c in countryXML.text.split("/")]
					metadata.countries.discard('')
				except: pass
				

				# COLLECTIONS (Set)    ----note_ there is only ONE set, so no need to loop
				# try:
					# mysetstruct = nfoXML.xpath("set")
					# Log("my set struct is : " + str(mysetstruct))
				# except:
					# Log("unable to log 'mysetstruct'")
					# pass
				mytemp = None
				try: 
					#mytemp = nfoXML.xpath("set")[0][0].text    #works :-)
					mytemp = nfoXML.xpath("set")[0].xpath("overview")[0].text  # also works and is more flexible
					Log("direct extraction BEFORE for-loop generated : " + str(mytemp))
				except: 
					mytemp = ""
					Log("Unable to set mytemp!!!")
					pass
				for mysetstruct in nfoXML.xpath("set"):
					try: Log("Set level TEXT is : " + str(mysetstruct[0]))
					except: pass
					try:
						mysetname = mysetstruct.xpath("name")   #[0].text
						#myname1 = myactor.xpath("name")[0].text
					except: 
						Log("NOT able to asign val mysetname, i.e. could not extract name tag from set XML")
						pass
					try: Log("set NAME XML is : " + str(mysetname))
					except:
						Log("unable to log 'mysetname'")
						pass
					try:
						mysetnametxtunsplit = mysetname[0].text   #was mysetname[0].text, but may not need the index as only elemebt
						Log("set name txt before split  is : " + str(mysetnametxtunsplit))
					except:
						Log("unable to log 'mysetnametxtunsplit'")
						pass
				#now fallback to direct name if no value assigned yet
				if not mytemp:
					#now try the old flat <set> tag
					try:
						mytemp = nfoXML.xpath("set")[0].text
						Log("Set info from flat-style xml is : " + mytemp)
					except:
						Log("Error when trying to read flat-style SET tag")
						pass
					
				# try:
					# mysetnametxtsplit = mysetnametxtunsplit.split("/")
					# DLog("set name txt AFTER split is : " + str(mysetnametxtsplit))
				# except:
					# Log("unable to log 'mysetnametxtsplit'")
					# pass
				# try:
					# mysetclean1 = mysetnametxtsplit.strip()
					# DLog("set name txt split AND cleaned (via strip) is : " + mysetclean1)
					# mysetclean2 = mysetnametxtsplit[0]
					# DLog("set name txt split AND cleaned (via item [0]) is : " + mysetclean1)
				# except:
					# pass
				# try:
					# sets = nfoXML.xpath('set')
					# metadata.collections.clear()
					# [metadata.collections.add(s.strip()) for setXML in sets for s in setXML.text.split("/")]
					# metadata.collections.discard('')
				# except: pass
				
				# Duration
				try:
					DLog ("Trying to read <durationinseconds> tag from .nfo file...")
					fileinfoXML = XML.ElementFromString(nfoText).xpath('fileinfo')[0]
					streamdetailsXML = fileinfoXML.xpath('streamdetails')[0]
					videoXML = streamdetailsXML.xpath('video')[0]
					runtime = videoXML.xpath("durationinseconds")[0].text.strip()
					metadata.duration = int(re.compile('^([0-9]+)').findall(runtime)[0]) * 1000 # s
				except:
					try:
						DLog ("Fallback to <runtime> tag from .nfo file...")
						runtime = nfoXML.xpath("runtime")[0].text.strip()
						metadata.duration = int(re.compile('^([0-9]+)').findall(runtime)[0]) * 60 * 1000 # ms
					except:
						DLog("No Duration in .nfo file.")
						pass
				
				try: Log("Duration is : " + str(metadata.duration))
				except: 
					Log("Was not able to log the metadata.duration field")
					pass

				# TAGS  --> to feed into COLLECTIONS
				for mytag in nfoXML.xpath('tag'):
					Log("mytag sub-XML is : " + str(mytag))
					mytagtxt = mytag.text.split("/")[0]
					#mytagtxt = mytag[0].text.strip()
					Log("mytag net text is : " + mytagtxt)
					
					# try: role.name = myactor.xpath("name")[0].text     ##changed from role.actor to role.name on 21-Nov-2016 as plex seems to read that
					# except:
						# role.name = "unknown"
				
					# try: role.role = myactor.xpath("role")[0].text
					# except:
						# role.role = "unknown"

					# try: role.photo = myactor.xpath("thumb")[0].text
					# except: pass

					
				# Actors
				metadata.roles.clear()
				for myactor in nfoXML.xpath('actor'):
					try: 
						myname1 = myactor.xpath("name")[0].text
						Log("my actorname 1 (before new role was generated) is : " + myname1)
					except: pass
					role = metadata.roles.new()
					try: role.name = myactor.xpath("name")[0].text     ##changed from role.actor to role.name on 21-Nov-2016 as plex seems to read that
					except:
						role.name = "unknown"
				
					try: role.role = myactor.xpath("role")[0].text
					except:
						role.role = "unknown"

					try: role.photo = myactor.xpath("thumb")[0].text
					except: pass
				### this is line 650 atm 20161121: try to add Photo URL at some point

				# Remote posters and fanarts are disabled for now; having them seems to stop the local artworks from being used.
				#(remote) posters
				#(local) poster
				#if posterData:
				#	metadata.posters[posterFilename] = Proxy.Media(posterData)
				#(remote) fanart
				#(local) fanart
				#if fanartData:
				#	metadata.art[fanartFilename] = Proxy.Media(fanartData)

				# Trailer Support of local trailer files (those feed to extras and do NOT count as Media)
				# A Trailer is identified by adding "-trailer" at the end of the filename
				if Prefs['trailer']:
					for f in os.listdir(folderpath):
						(fn, ext) = os.path.splitext(f)
						try:
							title = ""
							if fn.endswith('-trailer'):
									title = ' '.join(fn.split('-')[:-1])
							if fn == "trailer" or f.startswith ('movie-trailer'):
									title = metadata.title
							if title != "":
								metadata.extras.add(TrailerObject(title=title, file=os.path.join(folderpath, f)))
								DLog("Found trailer file " + os.path.join(folderpath, f))
								DLog("Trailer title:" + title)
						except:
							DLog("Exception adding trailer file!")


				Log("---------------------")
				Log("Movie nfo Information")
				Log("---------------------")
				try: Log("ID: " + str(metadata.guid))
				except: Log("ID: -")
				try: Log("Title: " + str(metadata.title))
				except: Log("Title: -")
				try: Log("Year: " + str(metadata.year))
				except: Log("Year: -")
				try: Log("Original: " + str(metadata.original_title))
				except: Log("Original: -")
				try: Log("Rating: " + str(metadata.rating))
				except: Log("Rating: -")
				try: Log("Content: " + str(metadata.content_rating))
				except: Log("Content: -")
				try: Log("Studio: " + str(metadata.studio))
				except: Log("Studio: -")
				try: Log("Premiere: " + str(metadata.originally_available_at))
				except: Log("Premiere: -")
				try: Log("Tagline: " + str(metadata.tagline))
				except: Log("Tagline: -")
				try: Log("Summary: " + str(metadata.summary))
				except: Log("Summary: -")
				Log("Writers:")
				#try: [Log("\t" + writer) for writer in metadata.writers]
				try: [Log("\t" + writer.name) for writer in metadata.writers]
				except: Log("\t-")
				Log("Directors:")
				try: [Log("\t" + director) for director in metadata.directors]
				except: Log("\t-")
				Log("Genres:")
				try: [Log("\t" + genre) for genre in metadata.genres]
				except: Log("\t-")
				Log("Countries:")
				try: [Log("\t" + country) for country in metadata.countries]
				except: Log("\t-")
				Log("Collections:")
				try: [Log("\t" + collection) for collection in metadata.collections]
				except: Log("\t-")
				try: Log("Duration: " + str(metadata.duration // 60000) + ' min')
				except: Log("Duration: -")
				Log("Actors:")
				try: [Log("\t" + actor.name + " > " + actor.role) for actor in metadata.roles]
				except: [Log("\t" + actor.name) for actor in metadata.roles]
				except: Log("\t-")
				Log("---------------------")
			else:
				Log("ERROR: No <movie> tag in " + nfoFile + ". Aborting!")
			return metadata
##### END of update Function #####



############################################################################################################################################################################################
# ------- this is now the TV SHOWS Class
############################################################################################################################################################################################

class xmlnfo(Agent.TV_Shows):
	name = 'XMLnfoImporter(TV Shows)'
	ver = '0.01'
	primary_provider = False
	languages = [Locale.Language.NoLanguage]
	#accepts_from = ['com.plexapp.agents.localmedia','com.plexapp.agents.opensubtitles','com.plexapp.agents.podnapisi','com.plexapp.agents.plexthememusic','com.plexapp.agents.subzero']
	contributes_to = ['com.plexapp.agents.thetvdb','com.plexapp.agents.thetvdbdvdorder','com.plexapp.agents.themoviedb','com.plexapp.agents.none']



################################# search function #############################################
	def search(self, results, media, lang):
		DLog("++++++++++++++++++++++++")
		DLog("Entering TV search function")
		DLog("++++++++++++++++++++++++")

		Log("" + self.name + " Version: " + self.ver)

		Log("Langage in search fct is : " + lang)
		try: Log("Media primary_metadata Variable is : " + str(media.primary_metadata))
		except:
			Log("Was not able to Log media.primary_metadata")
			pass
		try: Log("Media primary_agent Variable is : " + str(media.primary_agent))
		except:
			Log("Was not able to Log media.primary_agent")
			pass
		try: Log("Media filename Variable is : " + str(media.filename))
		except:
			Log("Was not able to Log media.filename")
			pass
		try: Log("Media ID Variable is : " + str(media.id))
		except:
			Log("Was not able to Log media.id")
			pass
		try: Log("Media GUID Variable is : " + str(media.guid))
		except:
			Log("Was not able to Log media.guid")
			pass
		try: Log("Media Name Variable is : " + media.name)
		except:
			Log("Was not able to Log media.name")
			pass
		try: Log("Media Year Variable is : " + str(media.year))
		except:
			Log("Was not able to Log media.year")
			pass
		try: Log("Media duration Variable is : " + str(media.duration))
		except:
			Log("Was not able to Log media.duration")
			pass
		try: Log("Media GUID Variable is : " + str(media.guid))
		except:
			Log("Was not able to Log media.guid")
			pass

		results.Append(MetadataSearchResult(id = 'null', score = 100))    #copied from localmedia agent - hoping that a SECONDARY Agent is ok to only do UPDATE

	#### probably need to comment OUT the below part of search fct- reason being that a secondary agent does NOT really do some matching.
#		self.DLog(media.primary_metadata)
#		filename = os.path.basename(String.Unquote(media.filename).encode('utf-8'))
#		path1 = os.path.dirname(String.Unquote(media.filename).encode('utf-8'))
#		self.DLog(path1)
#		path = os.path.dirname(path1)
#		nfoName = os.path.join(path, "tvshow.nfo")
#		self.DLog('Looking for TV Show NFO file at ' + nfoName)
#		if not os.path.exists(nfoName):
#			nfoName = os.path.join(path1, "tvshow.nfo")
#			self.DLog('Looking for TV Show NFO file at ' + nfoName)
#		if not os.path.exists(nfoName):
#			path2 = os.path.dirname(os.path.dirname(path))
#			nfoName = os.path.join(path2, "tvshow.nfo")
#			self.DLog('Looking for TV Show NFO file at ' + nfoName)
#
#		id = media.id
#		year = 0
#		if media.title:
#			title = media.title
#		else:
#			title = "Unknown"
#
#
#		if not os.path.exists(nfoName):
#			self.DLog("Couldn't find a tvshow.nfo file; will try to guess from filename...:")
#			regtv = re.compile('(.+?)'
#				'[ .]S(\d\d?)E(\d\d?)'
#				'.*?'
#				'(?:[ .](\d{3}\d?p)|\Z)?')
#			tv = regtv.match(filename)
#			if tv:
#				title = tv.group(1).replace(".", " ")
#			self.DLog("Using tvshow.title = " + title)
#		else:
#			nfoFile = nfoName
#			Log("Found nfo file at " + nfoFile)
#			nfoText = Core.storage.load(nfoFile)
#			# work around failing XML parses for things with &'s in them. This may need to go farther than just &'s....
#			nfoText = re.sub(r'&(?![A-Za-z]+[0-9]*;|#[0-9]+;|#x[0-9a-fA-F]+;)', r'&amp;', nfoText)
#			# remove empty xml tags from nfo
#			self.DLog('Removing empty XML tags from tvshows nfo...')
#			nfoText = re.sub(r'^\s*<.*/>[\r\n]+', '', nfoText, flags = re.MULTILINE)
#
#			nfoTextLower = nfoText.lower()
#			if nfoTextLower.count('<tvshow') > 0 and nfoTextLower.count('</tvshow>') > 0:
#				# Remove URLs (or other stuff) at the end of the XML file
#				nfoText = '%s</tvshow>' % nfoText.split('</tvshow>')[0]
#
#				#likely an xbmc nfo file
#				try: nfoXML = XML.ElementFromString(nfoText).xpath('//tvshow')[0]
#				except:
#					self.DLog('ERROR: Cant parse XML in ' + nfoFile + '. Aborting!')
#					return
#				Log(nfoXML.xpath("title"))
#
#				# Title
#				try: title = nfoXML.xpath("title")[0].text
#				except:
#					self.DLog("ERROR: No <title> tag in " + nfoFile + ". Aborting!")
#					return
#				# Sort Title
#				try: media.title_sort = nfoXML.xpath("sorttitle")[0].text
#				except:
#					self.DLog("No <sorttitle> tag in " + nfoFile + ".")
#					pass
#				# ID
#				try: id = nfoXML.xpath("id")[0].text
#				except:
#					id = None
#
#		# if tv show id doesn't exist, create
#		# one based on hash of title
#		if not id:
#			ord3 = lambda x : '%.3d' % ord(x)
#			id = int(''.join(map(ord3, title)))
#			id = str(abs(hash(int(id))))
#
#			Log('ID: ' + str(id))
#			Log('Title: ' + str(title))
#			Log('Year: ' + str(year))
#
#		results.Append(MetadataSearchResult(id=id, name=title, year=year, lang=lang, score=100))
#		Log('scraped results: ' + str(title) + ' | year = ' + str(year) + ' | id = ' + str(id))




#################### update Function #############################################
	def update(self, metadata, media, lang):
		DLog("++++++++++++++++++++++++++++")
		DLog("Entering TV  UPDATE function")
		DLog("++++++++++++++++++++++++++++")
		Log ("" + self.name + " Version: " + self.ver)





		Dict.Reset()
		metadata.duration = None
		id = media.id
		Log("The Media-ID is =  " + id)
		duration_key = 'duration_'+id
		Dict[duration_key] = [0] * 200
		Log('Update called for TV Show with id (media-id)= ' + id)
		try:
			filename=os.path.basename(media.items[0].parts[0].file)
			path1 = os.path.dirname(media.items[0].parts[0].file)
		except:
			pageUrl = "http://127.0.0.1:32400/library/metadata/" + id + "/tree"
			nfoXML = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MediaItem/MediaPart')[0]
			filename = os.path.basename(String.Unquote(nfoXML.get('file')))
			path1 = os.path.dirname(String.Unquote(nfoXML.get('file')))

		path = os.path.dirname(path1)

		nfoName = os.path.join(path, "tvshow.nfo")
		DLog('Looking for TV Show NFO file at ' + nfoName)
		if not os.path.exists(nfoName):
			nfoName = os.path.join(path1, "tvshow.nfo")
			DLog('Looking for TV Show NFO file at ' + nfoName)
			path = path1
		if not os.path.exists(nfoName):
			path2 = os.path.dirname(os.path.dirname(path))
			nfoName = os.path.join(path2, "tvshow.nfo")
			DLog('Looking for TV Show NFO file at ' + nfoName)
			path = path2
		if not os.path.exists(nfoName):
			path = os.path.dirname(path1)


#		posterNames = []
#		posterNames.append (os.path.join(path, "poster.jpg"))
#		posterNames.append (os.path.join(path, "folder.jpg"))
#		posterNames.append (os.path.join(path, "show.jpg"))
#		posterNames.append (os.path.join(path, "season-all-poster.jpg"))
#
#		# check possible poster file locations
#		Log("WILL the checkFilePaths work ???? =====================================================")
#		posterFilename = self.checkFilePaths (posterNames, 'poster')
#
#		if posterFilename:
#			posterData = Core.storage.load(posterFilename)
#			metadata.posters['poster.jpg'] = Proxy.Media(posterData)
#			Log('Found poster image at ' + posterFilename)
#
#		bannerNames = []
#		bannerNames.append (os.path.join(path, "banner.jpg"))
#		bannerNames.append (os.path.join(path, "folder-banner.jpg"))
#
#		# check possible banner file locations
#		bannerFilename = self.checkFilePaths (bannerNames, 'banner')
#
#		if bannerFilename:
#			bannerData = Core.storage.load(bannerFilename)
#			metadata.banners['banner.jpg'] = Proxy.Media(bannerData)
#			Log('Found banner image at ' + bannerFilename)
#
#		fanartNames = []
#
#		fanartNames.append (os.path.join(path, "fanart.jpg"))
#		fanartNames.append (os.path.join(path, "art.jpg"))
#		fanartNames.append (os.path.join(path, "backdrop.jpg"))
#		fanartNames.append (os.path.join(path, "background.jpg"))
#
#		# check possible fanart file locations
#		fanartFilename = self.checkFilePaths (fanartNames, 'fanart')
#
#		if fanartFilename:
#			fanartData = Core.storage.load(fanartFilename)
#			metadata.art['fanart.jpg'] = Proxy.Media(fanartData)
#			Log('Found fanart image at ' + fanartFilename)
#
#		themeNames = []
#
#		themeNames.append (os.path.join(path, "theme.mp3"))
#
#		# check possible theme file locations
#		themeFilename = self.checkFilePaths (themeNames, 'theme')
#
#		if themeFilename:
#			themeData = Core.storage.load(themeFilename)
#			metadata.themes['theme.mp3'] = Proxy.Media(themeData)
#			Log('Found theme music ' + themeFilename)
#
#		#### HERE I could try to start looking up the theme file from http://tvthemes.plexapp.com/id.mp3
#		### problem is that I don't have the TVDP ID yet (it is still in xml file, not parsed)
#

		if media.title:
			title = media.title
		else:
			title = "Unknown"

		if not os.path.exists(nfoName):
			DLog("Couldn't find a tvshow.nfo file; will try to guess from filename...:")
			regtv = re.compile('(.+?)'
				'[ .]S(\d\d?)E(\d\d?)'
				'.*?'
				'(?:[ .](\d{3}\d?p)|\Z)?')
			tv = regtv.match(filename)
			if tv:
				title = tv.group(1).replace(".", " ")
				metadata.title = title
			Log("Using tvshow.title = " + title)
		else:
			nfoFile = nfoName
			nfoText = Core.storage.load(nfoFile)
			# work around failing XML parses for things with &'s in them. This may need to go farther than just &'s....
			nfoText = re.sub(r'&(?![A-Za-z]+[0-9]*;|#[0-9]+;|#x[0-9a-fA-F]+;)', r'&amp;', nfoText)
			# remove empty xml tags from nfo
			DLog('Removing empty XML tags from tvshows nfo...')
			nfoText = re.sub(r'^\s*<.*/>[\r\n]+', '', nfoText, flags = re.MULTILINE)
			nfoTextLower = nfoText.lower()
			if nfoTextLower.count('<tvshow') > 0 and nfoTextLower.count('</tvshow>') > 0:
				# Remove URLs (or other stuff) at the end of the XML file
				nfoText = '%s</tvshow>' % nfoText.split('</tvshow>')[0]

				#likely an xbmc nfo file
				try: nfoXML = XML.ElementFromString(nfoText).xpath('//tvshow')[0]
				except:
					DLog('ERROR: Cant parse XML in ' + nfoFile + '. Aborting!')     #####  may also work with syntax:   DLog('ERROR: Cant parse XML in %s. Aborting!' % (nfoFile))
					return

				#remove remaining empty xml tags
				DLog('Removing remaining empty XML tags from tvshows nfo...')
				nfoXML = RemoveEmptyTags(nfoXML)

				# Title
				try: metadata.title = nfoXML.xpath("title")[0].text
				except:
					DLog("ERROR: No <title> tag in " + nfoFile + ". Aborting!")
					return
				### TVDB ID
				Log('---- the current Metadata-Id is = %s', metadata.id)
				Log('---- XML ID contains   %s', nfoXML.xpath("id")[0].text)
				try: metadata.id = nfoXML.xpath("id")[0].text
				except:
					DLog("No  TVDB <id> tag in " + nfoFile + ".")
					pass
				Log('------ NOW, the Metadata-Id is = %s', metadata.id)
                     # Sort Title
				try: metadata.title_sort = nfoXML.xpath("sorttitle")[0].text
				except:
					DLog("No <sorttitle> tag in " + nfoFile + ".")
					pass
				# Original Title
				try: metadata.original_title = nfoXML.xpath('originaltitle')[0].text
				except: pass
				# Content Rating
				try:
					mpaa = nfoXML.xpath('./mpaa')[0].text
					match = re.match(r'(?:Rated\s)?(?P<mpaa>[A-z0-9-+/.]+(?:\s[0-9]+[A-z]?)?)?', mpaa)
					if match.group('mpaa'):
						content_rating = match.group('mpaa')
					else:
						content_rating = 'NR'
					metadata.content_rating = content_rating
				except: pass
				# Network
				try: metadata.studio = nfoXML.xpath("studio")[0].text
				except: pass
				# Premiere
				try:
					air_string = None
					try:
						DLog("Reading aired tag...")
						air_string = nfoXML.xpath("aired")[0].text
						DLog("Aired tag is: " + air_string)
					except:
						DLog("No aired tag found...")
						pass
					if not air_string:
						try:
							DLog("Reading premiered tag...")
							air_string = nfoXML.xpath("premiered")[0].text
							DLog("Premiered tag is: " + air_string)
						except:
							DLog("No premiered tag found...")
							pass
					if not air_string:
						try:
							DLog("Reading dateadded tag...")
							air_string = nfoXML.xpath("dateadded")[0].text
							DLog("Dateadded tag is: " + air_string)
						except:
							DLog("No dateadded tag found...")
							pass
					if air_string:
						try:
							if Prefs['dayfirst']:
								dt = parse(air_string, dayfirst=True)
							else:
								dt = parse(air_string)
							metadata.originally_available_at = dt
							DLog("Set premiere to: " + dt.strftime('%Y-%m-%d'))
						except:
							DLog("Couldn't parse premiere: " + traceback.format_exc())
							pass
				except:
					DLog("Exception parsing Premiere: " + traceback.format_exc())
					pass

				# Tagline
				try: metadata.tagline = nfoXML.findall("tagline")[0].text
				except: pass

				# Summary (Plot)
				try: metadata.summary = nfoXML.xpath("plot")[0].text
				except:
					metadata.summary = ""
					pass

				# Ratings
				try:
					nforating = round(float(nfoXML.xpath("rating")[0].text.replace(',', '.')),1)
					metadata.rating = nforating
					DLog("Series Rating found: " + str(nforating))
				except:
					DLog("Can't read rating from tvshow.nfo.")
					nforating = 0.0
					pass
				if Prefs['altratings']:
					DLog("Searching for additional Ratings...")
					allowedratings = Prefs['ratings']
					if not allowedratings: allowedratings = ""
					addratingsstring = ""
					try:
						addratings = nfoXML.xpath('ratings')
						DLog("Trying to read additional ratings from tvshow.nfo.")
					except:
						DLog("Can't read additional ratings from tvshow.nfo.")
						pass
					if addratings:
						for addratingXML in addratings:
							for addrating in addratingXML:
								ratingprovider = str(addrating.attrib['moviedb'])
								ratingvalue = str(addrating.text.replace (',','.'))
								if ratingprovider.lower() in PERCENT_RATINGS:
									ratingvalue = ratingvalue + "%"
								if ratingprovider in allowedratings or allowedratings == "":
									self.DLog("adding rating: " + ratingprovider + ": " + ratingvalue)
									addratingsstring = addratingsstring + " | " + ratingprovider + ": " + ratingvalue
							DLog("Putting additional ratings at the " + Prefs['ratingspos'] + " of the summary!")
							if Prefs['ratingspos'] == "front":
								if Prefs['preserverating']:
									metadata.summary = addratingsstring[3:] + unescape(" &#9733;\n\n") + metadata.summary
								else:
									metadata.summary = unescape("&#9733; ") + addratingsstring[3:] + unescape(" &#9733;\n\n") + metadata.summary
							else:
								metadata.summary = metadata.summary + unescape("\n\n&#9733; ") + addratingsstring[3:] + unescape(" &#9733;")
					if Prefs['preserverating']:
						DLog("Putting .nfo rating in front of summary!")
						metadata.summary = unescape(str(Prefs['beforerating'])) + "{:.1f}".format(nforating) + unescape(str(Prefs['afterrating'])) + metadata.summary
						metadata.rating = nforating
					else:
						metadata.rating = nforating

				# Genres
				try:
					genres = nfoXML.xpath('genre')
					metadata.genres.clear()
					[metadata.genres.add(g.strip()) for genreXML in genres for g in genreXML.text.split("/")]
					metadata.genres.discard('')
				except: pass

				# Collections (Set)
				try:
					sets = nfoXML.xpath('set')
					metadata.collections.clear()
					[metadata.collections.add(s.strip()) for setXML in sets for s in setXML.text.split("/")]
					metadata.collections.discard('')
				except: pass

				# Duration
				try:
					sruntime = nfoXML.xpath("durationinseconds")[0].text
					metadata.duration = int(re.compile('^([0-9]+)').findall(sruntime)[0]) * 1000
				except:
					try:
						sruntime = nfoXML.xpath("runtime")[0].text
						duration = int(re.compile('^([0-9]+)').findall(sruntime)[0])
						duration_ms = xbmcnfotv.time_convert (self, duration)
						metadata.duration = duration_ms
						DLog("Set Series Episode Duration from " + str(duration) + " in tvshow.nfo file to " + str(duration_ms) + " in Plex.")
					except:
						DLog("No Series Episode Duration in tvschow.nfo file.")
						pass

				# Actors
				metadata.roles.clear()
				for actor in nfoXML.xpath('actor'):
					role = metadata.roles.new()
					try: role.name = actor.xpath("name")[0].text      ##changed from role.actor to role.name on 21-Nov-2016 as plex seems to read that
					except:
						role.name = "unknown"
					try: role.role = actor.xpath("role")[0].text
					except:
						role.role = "unknown"
					try: role.photo = actor.xpath("thumb")[0].text
					except: pass
					# if role.photo and role.photo != 'None' and role.photo != '':
						# data = HTTP.Request(actor.xpath("thumb")[0].text)
						# Log('Added Thumbnail for: ' + role.actor)


				Log("---------------------------------------------")
				Log("TV Show extracted Series nfo Information")
				Log("---------------------------------------------")
				try: Log("ID: " + str(metadata.guid))
				except: Log("ID: -")
				try: Log("Title: " + str(metadata.title))
				except: Log("Title: -")
				try: Log("TVDB-ID: " + str(metadata.id))
				except: Log("TVDB-ID: -")
				try: Log("Sort Title: " + str(metadata.title_sort))
				except: Log("Sort Title: -")
				try: Log("Original: " + str(metadata.original_title))
				except: Log("Original: -")
				try: Log("Rating: " + str(metadata.rating))
				except: Log("Rating: -")
				try: Log("Content: " + str(metadata.content_rating))
				except: Log("Content: -")
				try: Log("Network: " + str(metadata.studio))
				except: Log("Network: -")
				try: Log("Premiere: " + str(metadata.originally_available_at))
				except: Log("Premiere: -")
				try: Log("Tagline: " + str(metadata.tagline))
				except: Log("Tagline: -")
				try: Log("Summary: " + str(metadata.summary))
				except: Log("Summary: -")
				Log("Genres:")
				try: [Log("\t" + genre) for genre in metadata.genres]
				except: Log("\t-")
				Log("Collections:")
				try: [Log("\t" + collection) for collection in metadata.collections]
				except: Log("\t-")
				try: Log("Duration: " + str(metadata.duration // 60000) + ' min')
				except: Log("Duration: -")
				Log("Actors:")
				try: [Log("\t" + actor.name + " > " + actor.role) for actor in metadata.roles]
				except: [Log("\t" + actor.name) for actor in metadata.roles]
				except: Log("\t-")
				Log("---------------------")

		

           ##### Grabs the season data
		@parallelize
		def UpdateEpisodes():
			DLog("UpdateEpisodes called")
			pageUrl = "http://127.0.0.1:32400/library/metadata/" + media.id + "/children"
			DLog("pageURL is : " + pageUrl)
			seasonList = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/Directory')
			DLog("Season List is : " + str(seasonList))

			seasons = []
			for seasons in seasonList:
				try: seasonID = seasons.get('key')
				except: pass
				try: season_num = seasons.get('index')
				except: pass

				DLog("seasonID : " + path)
				if seasonID.count('allLeaves') == 0:
					DLog("Finding episodes")

					pageUrl = "http://127.0.0.1:32400" + seasonID
					DLog("pageURL is : " + pageUrl)

					episodes = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/Video')
					DLog("Found " + str(len(episodes)) + " episodes.")

					firstEpisodePath = XML.ElementFromURL(pageUrl).xpath('//Part')[0].get('file')
					seasonPath = os.path.dirname(firstEpisodePath)

					# seasonFilename = ""
					# seasonFilenameZero = ""
					# seasonPathFilename = ""
					# if(int(season_num) == 0):
						# seasonFilenameFrodo = 'season-specials-poster.jpg'
						# seasonFilenameEden = 'season-specials.tbn'
						# seasonFilenameZero = 'season00-poster.jpg'
					# else:
						# seasonFilenameFrodo = 'season%(number)02d-poster.jpg' % {"number": int(season_num)}
						# seasonFilenameEden = 'season%(number)02d.tbn' % {"number": int(season_num)}

					# seasonPosterNames = []

					# #Frodo
					# seasonPosterNames.append (os.path.join(path, seasonFilenameFrodo))
					# seasonPosterNames.append (os.path.join(path, seasonFilenameZero))
					# seasonPosterNames.append (os.path.join(seasonPath, seasonFilenameFrodo))
					# seasonPosterNames.append (os.path.join(seasonPath, seasonFilenameZero))
					# #Eden
					# seasonPosterNames.append (os.path.join(path, seasonFilenameEden))
					# seasonPosterNames.append (os.path.join(seasonPath, seasonFilenameEden))
					# #DLNA
					# seasonPosterNames.append (os.path.join(seasonPath, "folder.jpg"))
					# seasonPosterNames.append (os.path.join(seasonPath, "poster.jpg"))
					# #Fallback to Series Poster
					# seasonPosterNames.append (os.path.join(path, "poster.jpg"))

					# # check possible season poster file locations
					# seasonPosterFilename = self.checkFilePaths (seasonPosterNames, 'season poster')

					# if seasonPosterFilename:
						# seasonData = Core.storage.load(seasonPosterFilename)
						# metadata.seasons[season_num].posters[seasonFilename] = Proxy.Media(seasonData)
						# Log('Found season poster image at ' + seasonPosterFilename)

					


					episodeXML = []
					epnumber = 0
					for episodeXML in episodes:
						ep_key = episodeXML.get('key')
						DLog("epKEY: " + ep_key)
						epnumber = epnumber + 1
						ep_num = episodeXML.get('index')
						if (ep_num == None):
							DLog("epNUM: Error!")
							ep_num = str(epnumber)
						DLog("epNUM: " + ep_num)

						# Get the episode object from the model
						episode = metadata.seasons[season_num].episodes[ep_num]

						# Grabs the episode information
						@task
						def UpdateEpisode(episode=episode, season_num=season_num, ep_num=ep_num, ep_key=ep_key, path=path1):
							DLog("UpdateEpisode called for episode (" + str(episode)+ ", " + str(ep_key) + ") S" + str(season_num.zfill(2)) + "E" + str(ep_num.zfill(2)))
							if(ep_num.count('allLeaves') == 0):
								pageUrl = "http://127.0.0.1:32400" + ep_key + "/tree"
								path1 = XML.ElementFromURL(pageUrl).xpath('//MediaPart')[0].get('file')
								DLog("UPDATE:                       " + path1)
								filepath = path1.split
								path = os.path.dirname(path1)
								fileExtension = path1.split(".")[-1].lower()

								nfoFile = path1.replace('.'+fileExtension, '.nfo')
								DLog("Looking for episode NFO file: " + nfoFile)
								if os.path.exists(nfoFile):
									DLog("File exists...")
									nfoText = Core.storage.load(nfoFile)
									# strip media browsers <multiepisodenfo> tags
									nfoText = nfoText.replace ('<multiepisodenfo>','')
									nfoText = nfoText.replace ('</multiepisodenfo>','')
									# work around failing XML parses for things with &'s in them. This may need to go farther than just &'s....
									nfoText = re.sub(r'&(?![A-Za-z]+[0-9]*;|#[0-9]+;|#x[0-9a-fA-F]+;)', r'&amp;', nfoText)
									# remove empty xml tags from nfo
									DLog('Removing empty XML tags from tvshows nfo...')
									nfoText = re.sub(r'^\s*<.*/>[\r\n]+', '', nfoText, flags = re.MULTILINE)
									nfoTextLower = nfoText.lower()
									if nfoTextLower.count('<episodedetails') > 0 and nfoTextLower.count('</episodedetails>') > 0:
										DLog("Looks like an XBMC NFO file (has <episodedetails>)")
										nfoepc = int(nfoTextLower.count('<episodedetails'))
										nfopos = 1
										multEpTitlePlexPatch = multEpSummaryPlexPatch = ""
										multEpTestPlexPatch = 0
										while nfopos <= nfoepc:
											DLog("EpNum: " + str(ep_num) + " NFOEpCount:" + str(nfoepc) +" Current EpNFOPos: " + str(nfopos))
											# Remove URLs (or other stuff) at the end of the XML file
											nfoTextTemp = '%s</episodedetails>' % nfoText.split('</episodedetails>')[nfopos-1]

											# likely an xbmc nfo file
											try: nfoXML = XML.ElementFromString(nfoTextTemp).xpath('//episodedetails')[0]
											except:
												DLog('ERROR: Cant parse XML in file: ' + nfoFile)
												return

											# remove remaining empty xml tags
											DLog('Removing remaining empty XML Tags from episode nfo...')
											nfoXML = RemoveEmptyTags(nfoXML)

											# check ep number
											nfo_ep_num = 0
											try:
												nfo_ep_num = nfoXML.xpath('episode')[0].text
												DLog('EpNum from NFO: ' + str(nfo_ep_num))
											except: pass

											# Checks to see user has renamed files so plex ignores multiepisodes and confirms that there is more than on episodedetails
											if not re.search('.s\d{1,3}e\d{1,3}[-]?e\d{1,3}.', path1.lower()) and (nfoepc > 1):
												multEpTestPlexPatch = 1

											# Creates combined strings for Plex MultiEpisode Patch
											if multEpTestPlexPatch and Prefs['multEpisodePlexPatch'] and (nfoepc > 1):
												DLog('Multi Episode found: ' + str(nfo_ep_num))
												multEpTitleSeparator = Prefs['multEpisodeTitleSeparator']
												try:
													if nfopos == 1:
														multEpTitlePlexPatch = nfoXML.xpath('title')[0].text
														multEpSummaryPlexPatch = "[Episode #" + str(nfo_ep_num) + " - " + nfoXML.xpath('title')[0].text + "] " + nfoXML.xpath('plot')[0].text
													else:
														multEpTitlePlexPatch = multEpTitlePlexPatch + multEpTitleSeparator + nfoXML.xpath('title')[0].text
														multEpSummaryPlexPatch = multEpSummaryPlexPatch + "\n" + "[Episode #" + str(nfo_ep_num) + " - " + nfoXML.xpath('title')[0].text + "] " + nfoXML.xpath('plot')[0].text
												except: pass
											else:
												if int(nfo_ep_num) == int(ep_num):
													nfoText = nfoTextTemp
													break

											nfopos = nfopos + 1

										if (not multEpTestPlexPatch or not Prefs['multEpisodePlexPatch']) and (nfopos > nfoepc):
											DLog('No matching episode in nfo file!')
											return

										# Ep. Title
										if Prefs['multEpisodePlexPatch'] and (multEpTitlePlexPatch != ""):
											DLog('using multi title: ' + multEpTitlePlexPatch)
											episode.title = multEpTitlePlexPatch
										else:
											try: episode.title = nfoXML.xpath('title')[0].text
											except:
												DLog("ERROR: No <title> tag in " + nfoFile + ". Aborting!")
												return
										# Ep. Content Rating
										try:
											mpaa = nfoXML.xpath('./mpaa')[0].text
											match = re.match(r'(?:Rated\s)?(?P<mpaa>[A-z0-9-+/.]+(?:\s[0-9]+[A-z]?)?)?', mpaa)
											if match.group('mpaa'):
												content_rating = match.group('mpaa')
											else:
												content_rating = 'NR'
											episode.content_rating = content_rating
										except: pass
										# Ep. Premiere
										try:
											air_string = None
											try:
												DLog("Reading aired tag...")
												air_string = nfoXML.xpath("aired")[0].text
												DLog("Aired tag is: " + air_string)
											except:
												DLog("No aired tag found...")
												pass
											if not air_string:
												try:
													DLog("Reading dateadded tag...")
													air_string = nfoXML.xpath("dateadded")[0].text
													DLog("Dateadded tag is: " + air_string)
												except:
													DLog("No dateadded tag found...")
													pass
											if air_string:
												try:
													if Prefs['dayfirst']:
														dt = parse(air_string, dayfirst=True)
													else:
														dt = parse(air_string)
													episode.originally_available_at = dt
													DLog("Set premiere to: " + dt.strftime('%Y-%m-%d'))
												except:
													DLog("Couldn't parse premiere: " + air_string)
													pass
										except:
											DLog("Exception parsing Ep Premiere: " + traceback.format_exc())
											pass
										# Ep. Summary
										if Prefs['multEpisodePlexPatch'] and (multEpSummaryPlexPatch != ""):
											DLog('using multi summary: ' + multEpSummaryPlexPatch)
											episode.summary = multEpSummaryPlexPatch
										else:
											try: episode.summary = nfoXML.xpath('plot')[0].text
											except:
												episode.summary = ""
												pass
										# Ep. Ratings
										try:
											epnforating = round(float(nfoXML.xpath("rating")[0].text.replace(',', '.')),1)
											episode.rating = epnforating
											DLog("Episode Rating found: " + str(epnforating))
										except:
											DLog("Cant read rating from episode nfo.")
											epnforating = 0.0
											pass
										if Prefs['altratings']:
											DLog("Searching for additional episode ratings...")
											allowedratings = Prefs['ratings']
											if not allowedratings: allowedratings = ""
											addepratingsstring = ""
											try:
												addepratings = nfoXML.xpath('ratings')
												DLog("Additional episode ratings found: " + str(addeprating))
											except:
												DLog("Can't read additional episode ratings from nfo.")
												pass
											if addepratings:
												for addepratingXML in addepratings:
													for addeprating in addepratingXML:
														epratingprovider = str(addeprating.attrib['moviedb'])
														epratingvalue = str(addeprating.text.replace (',','.'))
														if epratingprovider.lower() in PERCENT_RATINGS:
															epratingvalue = epratingvalue + "%"
														if epratingprovider in allowedratings or allowedratings == "":
															DLog("adding episode rating: " + epratingprovider + ": " + epratingvalue)
															addepratingsstring = addepratingsstring + " | " + epratingprovider + ": " + epratingvalue
												DLog("Putting additional episode ratings at the " + Prefs['ratingspos'] + " of the summary!")
												if Prefs['ratingspos'] == "front":
													if Prefs['preserveratingep']:
														episode.summary = addepratingsstring[3:] + unescape(" &#9733;\n\n") + episode.summary
													else:
														episode.summary = unescape("&#9733; ") + addepratingsstring[3:] + unescape(" &#9733;\n\n") + episode.summary
												else:
													episode.summary = episode.summary + unescape("\n\n&#9733; ") + addepratingsstring[3:] + unescape(" &#9733;")
											if Prefs['preserveratingep']:
												DLog("Putting Ep .nfo rating in front of summary!")
												episode.summary = unescape(str(Prefs['beforeratingep'])) + "{:.1f}".format(epnforating) + unescape(str(Prefs['afterratingep'])) + episode.summary
												episode.rating = epnforating
											else:
												episode.rating = epnforating
										# Ep. Producers / Writers / Guest Stars(Credits)
										try:
											credit_string = None
											credits = nfoXML.xpath('credits')
											episode.producers.clear()
											episode.writers.clear()
											episode.guest_stars.clear()
											for creditXML in credits:
												for credit in creditXML.text.split("/"):
													credit_string = credit.strip()
													DLog ("Credit String: " + credit_string)
													if " (Producer)" in credit_string:
														DLog ("Credit (Producer): " + credit_string)
														episode.producers.add(credit_string.replace(" (Producer)",""))
														continue
													if " (Guest Star)" in credit_string:
														DLog ("Credit (Guest Star): " + credit_string)
														credit_string.replace(" (Guest Star)","")
														episode.guest_stars.add(credit_string)
														continue
													if " (Writer)" in credit_string:
														DLog ("Credit (Writer): " + credit_string)
														credit_string.replace(" (Writer)","")
														episode.writers.add(credit_string)
														continue
													DLog ("Unknown Credit (adding as Writer): " + credit_string)
													episode.writers.add (credit_string)
										except:
											DLog("Exception parsing Credits: " + traceback.format_exc())
											pass
										# Ep. Directors
										try:
											directors = nfoXML.xpath('director')
											episode.directors.clear()
											for directorXML in directors:
												for director in directorXML.text.split("/"):
													director_string = director.strip()
													DLog ("Director: " + director)
													episode.directors.add(director)
										except:
											DLog("Exception parsing Director: " + traceback.format_exc())
											pass
										# Ep. Duration
										try:
											DLog ("Trying to read <durationinseconds> tag from episodes .nfo file...")
											fileinfoXML = XML.ElementFromString(nfoText).xpath('fileinfo')[0]
											streamdetailsXML = fileinfoXML.xpath('streamdetails')[0]
											videoXML = streamdetailsXML.xpath('video')[0]
											eruntime = videoXML.xpath("durationinseconds")[0].text
											eduration_ms = int(re.compile('^([0-9]+)').findall(eruntime)[0]) * 1000
											episode.duration = eduration_ms
										except:
											try:
												DLog ("Fallback to <runtime> tag from episodes .nfo file...")
												eruntime = nfoXML.xpath("runtime")[0].text
												eduration = int(re.compile('^([0-9]+)').findall(eruntime)[0])
												eduration_ms = xbmcnfotv.time_convert (self, eduration)
												episode.duration = eduration_ms
											except:
												episode.duration = metadata.duration if metadata.duration else None
												DLog ("No Episode Duration in episodes .nfo file.")
												pass
										try:
											if (eduration_ms > 0):
												eduration_min = int(round (float(eduration_ms) / 1000 / 60))
												Dict[duration_key][eduration_min] = Dict[duration_key][eduration_min] + 1
										except:
											pass

										# episodeThumbNames = []

										# #Multiepisode nfo thumbs
										# if (nfoepc > 1) and (not Prefs['multEpisodePlexPatch'] or not multEpTestPlexPatch):
											# for name in glob.glob1(os.path.dirname(nfoFile), '*S' + str(season_num.zfill(2)) + 'E' + str(ep_num.zfill(2)) + '*.*'):
												# if "-E" in name: continue
												# episodeThumbNames.append (os.path.join(os.path.dirname(nfoFile), name))

										# #Frodo
										# episodeThumbNames.append (nfoFile.replace('.nfo', '-thumb.jpg'))
										# #Eden
										# episodeThumbNames.append (nfoFile.replace('.nfo', '.tbn'))
										# #DLNA
										# episodeThumbNames.append (nfoFile.replace('.nfo', '.jpg'))

										# # check possible episode thumb file locations
										# episodeThumbFilename = self.checkFilePaths (episodeThumbNames, 'episode thumb')

										# if episodeThumbFilename:
											# thumbData = Core.storage.load(episodeThumbFilename)
											# episode.thumbs[episodeThumbFilename] = Proxy.Media(thumbData)
											# Log('Found episode thumb image at ' + episodeThumbFilename)

										Log("---------------------------------------------------------")
										Log("Episode (S"+season_num.zfill(2)+"E"+ep_num.zfill(2)+") nfo Information")
										Log("---------------------------------------------------------")
										try: Log("Title: " + str(episode.title))
										except: Log("Title: -")
										try: Log("Content: " + str(episode.content_rating))
										except: Log("Content: -")
										try: Log("Rating: " + str(episode.rating))
										except: Log("Rating: -")
										try: Log("Premiere: " + str(episode.originally_available_at))
										except: Log("Premiere: -")
										try: Log("Summary: " + str(episode.summary))
										except: Log("Summary: -")
										Log("Writers:")
										try: [Log("\t" + writer) for writer in episode.writers]
										except: Log("\t-")
										Log("Directors:")
										try: [Log("\t" + director) for director in episode.directors]
										except: Log("\t-")
										try: Log("Duration: " + str(episode.duration // 60000) + ' min')
										except: Log("Duration: -")
										Log("---------------------")
									else:
										Log("ERROR: <episodedetails> tag not found in episode NFO file " + nfoFile)

		# Final Steps
		duration_min = 0
		duration_string = ""
		if not metadata.duration:
			try:
				duration_min = Dict[duration_key].index(max(Dict[duration_key]))
				for d in Dict[duration_key]:
					if (d != 0):
						duration_string = duration_string + "(" + str(Dict[duration_key].index(d)) + "min:" + str(d) + ")"
			except:
				DLog("Error accessing duration_key in dictionary!")
				pass
			DLog("Episode durations are: " + duration_string)
			metadata.duration = duration_min * 60 * 1000
			DLog("Set Series Episode Runtime to median of all episodes: " + str(metadata.duration) + " (" + str (duration_min) + " minutes)")
		else:
			DLog("Series Episode Runtime already set! Current value is:" + str(metadata.duration))
		Dict.Reset()

