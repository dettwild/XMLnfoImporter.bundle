# XMLnfoImporter
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
import os, re, time, datetime, platform, traceback, re, htmlentitydefs

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

class xmlnfo(Agent.Movies):
	name = 'XML nfo Importer (Movies)'
	ver = '0.01'
	primary_provider = False
	#fallback_agent = 'com.plexapp.agents.imdb'
	languages = [Locale.Language.NoLanguage]    #dd 20161123: should work, could also try Locale.Language.English
	#accepts_from = ['com.plexapp.agents.localmedia','com.plexapp.agents.imdb','com.plexapp.agents.opensubtitles','com.plexapp.agents.podnapisi']
	contributes_to = ['com.plexapp.agents.imdb','com.plexapp.agents.themoviedb', 'com.plexapp.agents.none','com.plexapp.agents.data18']    #added by dd 21-Nov-2016, hoping to get XML readings in normal 'Plex Movie' Agent as well





############## helper functions #####
	def DLog (self, LogMessage):
		if Prefs['debug']:
			Log (LogMessage)

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
			self.DLog("Moviename from folder (withYear): " + moviename)
		else:
			if foldersplit[-1] == 'VIDEO_TS':
				moviename = os.sep.join(foldersplit[1:len(foldersplit)-1:]) + os.sep + re.sub (r' \(.*\)',r'',foldersplit[-2])
			else:
				moviename = os.sep.join(foldersplit) + os.sep + re.sub (r' \(.*\)',r'',foldersplit[-1])
			self.DLog("Moviename from folder: " + moviename)
		return moviename

	
	def checkFilePaths(self, pathfns, ftype):
		for pathfn in pathfns:
			self.DLog("Trying " + pathfn)
			if not os.path.exists(pathfn):
				continue
			else:
				Log("Found " + ftype + " file " + pathfn)
				return pathfn
		else:
			Log("No " + ftype + " file found! Aborting!")

	
	###### function to remove empty tags from a XML structure -- used to 'clean up'
	def RemoveEmptyTags(self, xmltags):
		for xmltag in xmltags.iter("*"):
			if len(xmltag):
				continue
			if not (xmltag.text and xmltag.text.strip()):
				self.DLog("Removing empty XMLTag: " + xmltag.tag)
				xmltag.getparent().remove(xmltag)
		return xmltags

	def FloatRound(self, x):
		return x + 0.5 / 2 - ((x + 0.5 / 2) % 0.5)

	##
	# Removes HTML or XML character references and entities from a text string.
	# Copyright: http://effbot.org/zone/re-sub.htm October 28, 2006 | Fredrik Lundh
	# @param text The HTML (or XML) source text.
	# @return The plain text, as a Unicode string, if necessary.

	def unescape(self, text):
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





##### search function #####
	def search(self, results, media, lang):
		self.DLog("++++++++++++++++++++++++")
		self.DLog("Entering search function")
		self.DLog("++++++++++++++++++++++++")
		Log("" + self.name + " Version: " + self.ver)

		Log("Langage in search fct is : " + lang)
		try: Log("Media filename Variable is : " + str(media.filename))
		except:
			Log("Was not able to Log media.filename")
			pass
		try: Log("Media ID Variable is : " + str(media.id))
		except:
			Log("Was not able to Log media.id")
			pass
		try: Log("Media Name Variable is : " + media.name)
		except:
			Log("Was not able to Log media.name")
			pass

		try: 
			path1 = String.Unquote(media.filename)
			folderpath = os.path.dirname(path1)
			self.DLog('folderpath: ' + folderpath)
		except:
			Log("Sth wrong with media filename")
			pass

		# Moviename with year from folder
		movienamewithyear = self.getMovieNameFromFolder (folderpath, True)
		# Moviename from folder
		moviename = self.getMovieNameFromFolder (folderpath, False)

		nfoNames = []    #initialisation to empty array
		# KODI naming
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
		try: self.Dlog("the nfo file in variable nfoFile is :" + nfoFile)
		except: pass

		if nfoFile:
			nfoText = Core.storage.load(nfoFile)
			# work around failing XML parses for things with &'s in
			# them. This may need to go farther than just &'s....
			nfoText = re.sub(r'&(?![A-Za-z]+[0-9]*;|#[0-9]+;|#x[0-9a-fA-F]+;)', r'&amp;', nfoText)
			nfoTextLower = nfoText.lower()

			if nfoTextLower.count('<movie') > 0 and nfoTextLower.count('</movie>') > 0:
				# Remove URLs (or other stuff) at the end of the XML file
				nfoText = '%s</movie>' % nfoText.rsplit('</movie>', 1)[0]

				# likely an xbmc nfo file
				try: nfoXML = XML.ElementFromString(nfoText).xpath('//movie')[0]
				except:
					self.DLog('ERROR: Cant parse XML in ' + nfoFile + '. Aborting!')
					return

				# Title
				try: media.name = nfoXML.xpath('title')[0].text
				except:
					self.DLog("ERROR: No <title> tag in " + nfoFile + ". Aborting!")
					return
				# Year
				try: media.year = nfoXML.xpath('year')[0].text
				except: pass
				# ID
				try:
					id = nfoXML.xpath('id')[0].text.strip()
				except:
					id=""
					pass
				if len(id) > 2:
						media.id = id
						self.DLog("ID from nfo: " + media.id)
				else:
					# if movie id doesn't exist, create
					# one based on hash of title and year
					ord3 = lambda x : '%.3d' % ord(x)
					id = int(''.join(map(ord3, media.name+str(media.year))))
					id = str(abs(hash(int(id))))
					media.id = id
					self.DLog("ID generated: " + media.id)

				results.Append(MetadataSearchResult(id=media.id, name=media.name, year=media.year, lang=lang, score=100))
				try: Log('Found movie information in NFO file: title = ' + media.name + ', year = ' + str(media.year) + ', id = ' + media.id)
				except: pass
			else:
				Log("ERROR: No <movie> tag in " + nfoFile + ". Aborting!")





##### update Function #####
	def update(self, metadata, media, lang):
		self.DLog("++++++++++++++++++++++++")
		self.DLog("Entering update function")
		self.DLog("++++++++++++++++++++++++")
		Log ("" + self.name + " Version: " + self.ver)
		
		#self.DLog("metadata overall data :" + metadata)
		Log ("Langage in update fct is : " + lang)

		parse_date = lambda s: Datetime.ParseDate(s).date()
		path1 = media.items[0].parts[0].file
		self.DLog('media file: ' + path1)
		folderpath = os.path.dirname(path1)
		self.DLog('folderpath: ' + folderpath)
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
			if nfoTextLower.count('<movie') > 0 and nfoTextLower.count('</movie>') > 0:
				# Remove URLs (or other stuff) at the end of the XML file
				nfoText = '%s</movie>' % nfoText.rsplit('</movie>', 1)[0]

				# likely an xbmc nfo file
				try: nfoXML = XML.ElementFromString(nfoText).xpath('//movie')[0]
				except:
					self.DLog('ERROR: Cant parse XML in ' + nfoFile + '. Aborting!')
					return

				#remove empty xml tags
				self.DLog('Removing empty XML tags from movies nfo...')
				nfoXML = self.RemoveEmptyTags(nfoXML)

				# Title     --edited (made 3 lines out of one with temp var mytitle to improve LOG and test coding
				try: 
					mytitle= nfoXML.xpath('title')[0].text.strip()
					Log("mytitle is :" + mytitle)
				except:
					Log("Can't assign Title value to variable mytitle")
					return
				
				if mytitle != '':
					Log("XML Title is : " + mytitle)
					metadata.title = mytitle
					Log("metadata title is : " + metadata.title)
				#except:
				#	self.DLog("ERROR: No <title> tag in " + nfoFile + ". Aborting!")
				#	return
				
				# Year
				try: metadata.year = int(nfoXML.xpath("year")[0].text.strip())
				except: pass
				
				# Original Title
				try: metadata.original_title = nfoXML.xpath('originaltitle')[0].text.strip()
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
						self.DLog('MPAA Rating: ' + mpaa_rating)
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
					self.DLog('Content Rating(s): ' + str(content_rating))
				except: pass
				if Prefs['country'] != '':
					cc = COUNTRY_CODES[Prefs['country']].split(',')
					self.DLog('Country code from settings: ' + Prefs['country'] + ':' + str(cc))
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

				# Studio
				try: metadata.studio = nfoXML.xpath("studio")[0].text.strip()
				except: pass
				
				# Premiere / Release Date
				try:
					release_string = None
					try:
						self.DLog("Reading releasedate tag...")
						release_string = nfoXML.xpath("releasedate")[0].text.strip()
						self.DLog("Releasedate tag is: " + release_string)
					except:
						self.DLog("No releasedate tag found...")
						pass
					if not release_string:
						try:
							self.DLog("Reading premiered tag...")
							release_string = nfoXML.xpath("premiered")[0].text.strip()
							self.DLog("Premiered tag is: " + release_string)
						except:
							self.DLog("No premiered tag found...")
							pass
					if not release_string:
						try:
							self.DLog("Reading dateadded tag...")
							release_string = nfoXML.xpath("dateadded")[0].text.strip()
							self.DLog("Dateadded tag is: " + release_string)
						except:
							self.DLog("No dateadded tag found...")
							pass
					if release_string:
						if not Prefs['correctdate']:
							release_date = parse_date(release_string)
						else:
							self.DLog("Apply date correction: " + Prefs['datestring'])
							if '*' in Prefs['datestring']:
								for char in ['/','-','.']:
									try:
										release_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(release_string, Prefs['datestring'].replace('*', char)))).date()
										self.DLog("Match found: " + Prefs['datestring'].replace('*', char))
									except: pass
							else:
								release_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(release_string, Prefs['datestring']))).date()
				except:
					self.DLog("Exception parsing releasedate: " + traceback.format_exc())
					pass
				try:
					if not release_date:
						self.DLog("Fallback to year tag instead...")
						release_date = time.strptime(str(metadata.year) + "-01-01", "%Y-%m-%d")
						metadata.originally_available_at = datetime.datetime.fromtimestamp(time.mktime(release_date)).date()
					else:
						self.DLog("Setting releasedate...")
						metadata.originally_available_at = release_date
				except: pass

				# Tagline
				try: metadata.tagline = nfoXML.xpath("tagline")[0].text.strip()
				except: pass
				try: self.Dlog("Tagline is : " + metadata.tagline)
				except: 
					Log("was not able to log the metadata.tagline field")
					pass
				
				# Summary (Outline/Plot)
				try:
					if Prefs['plot']:
						self.DLog("User setting forces plot before outline...")
						stype1 = 'plot'
						stype2 = 'outline'
					else:
						self.DLog("Default setting forces outline before plot...")
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
					self.DLog("Exception on reading summary!")
					pass
				
				try: self.Dlog("Summary is : " + metadata.summary)
				except: pass
				
				# Ratings
				try:
					nforating = float(nfoXML.xpath("rating")[0].text.replace(',', '.'))
					if Prefs['fround']:
						rating = self.FloatRound(nforating)
					else:
						rating = nforating
					if Prefs['altratings']:
						self.DLog("Searching for additional Ratings...")
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
										self.DLog("adding rating: " + ratingprovider + ": " + ratingvalue)
										addratingsstring = addratingsstring + " | " + ratingprovider + ": " + ratingvalue
							self.DLog("Putting additional ratings at the " + Prefs['ratingspos'] + " of the summary!")
							if Prefs['ratingspos'] == "front":
								if Prefs['preserverating']:
									metadata.summary = addratingsstring[3:] + self.unescape(" &#9733;\n\n") + metadata.summary
								else:
									metadata.summary = self.unescape("&#9733; ") + addratingsstring[3:] + self.unescape(" &#9733;\n\n") + metadata.summary
							else:
								metadata.summary = metadata.summary + self.unescape("\n\n&#9733; ") + addratingsstring[3:] + self.unescape(" &#9733;")
					if Prefs['preserverating']:
						self.DLog("Putting .nfo rating in front of summary!")
						metadata.summary = self.unescape(str(Prefs['beforerating'])) + "{:.1f}".format(nforating) + self.unescape(str(Prefs['afterrating'])) + metadata.summary
						metadata.rating = rating
					else:
						metadata.rating = rating
				except:
					self.DLog("Exception parsing ratings: " + traceback.format_exc())
					pass
				
				try: self.Dlog("Rating is : " + metadata.rating)
				except: 
					Log("was not able to log the metadata.rating field")
					pass				

				# Writers (Credits)
				try:
					credits = nfoXML.xpath('credits')
					metadata.writers.clear()
					[metadata.writers.add(c.strip()) for creditXML in credits for c in creditXML.text.split("/")]
					metadata.writers.discard('')
				except: pass
				# Directors
				try:
					directors = nfoXML.xpath('director')
					metadata.directors.clear()
					[metadata.directors.add(d.strip()) for directorXML in directors for d in directorXML.text.split("/")]
					metadata.directors.discard('')
				except: pass
				# Genres
				try:
					genres = nfoXML.xpath('genre')
					metadata.genres.clear()
					[metadata.genres.add(g.strip()) for genreXML in genres for g in genreXML.text.split("/")]
					metadata.genres.discard('')
				except: pass
				# Countries
				try:
					countries = nfoXML.xpath('country')
					metadata.countries.clear()
					[metadata.countries.add(c.strip()) for countryXML in countries for c in countryXML.text.split("/")]
					metadata.countries.discard('')
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
					self.DLog ("Trying to read <durationinseconds> tag from .nfo file...")
					fileinfoXML = XML.ElementFromString(nfoText).xpath('fileinfo')[0]
					streamdetailsXML = fileinfoXML.xpath('streamdetails')[0]
					videoXML = streamdetailsXML.xpath('video')[0]
					runtime = videoXML.xpath("durationinseconds")[0].text.strip()
					metadata.duration = int(re.compile('^([0-9]+)').findall(runtime)[0]) * 1000 # s
				except:
					try:
						self.DLog ("Fallback to <runtime> tag from .nfo file...")
						runtime = nfoXML.xpath("runtime")[0].text.strip()
						metadata.duration = int(re.compile('^([0-9]+)').findall(runtime)[0]) * 60 * 1000 # ms
					except:
						self.DLog("No Duration in .nfo file.")
						pass
				
				try: Log("Duration is : " + metadata.duration)
				except: 
					Log("Was not able to log the metadata.duration field")
					pass

				# Actors
				metadata.roles.clear()
				for actor in nfoXML.xpath('actor'):
					role = metadata.roles.new()
					try: role.name = actor.xpath("name")[0].text     ##changed from role.actor to role.name on 21-Nov-2016 as plex seems to read that
					except:
						role.name = "unknown"
				
					try: role.role = actor.xpath("role")[0].text
					except:
						role.role = "unknown"

				### this is line 650 atm 20161121: try to add Photo URL at some point

				# Remote posters and fanarts are disabled for now; having them seems to stop the local artworks from being used.
				#(remote) posters
				#(local) poster
				if posterData:
					metadata.posters[posterFilename] = Proxy.Media(posterData)
				#(remote) fanart
				#(local) fanart
				if fanartData:
					metadata.art[fanartFilename] = Proxy.Media(fanartData)

				# Trailer Support
				# Eden / Frodo
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
								self.DLog("Found trailer file " + os.path.join(folderpath, f))
								self.DLog("Trailer title:" + title)
						except:
							self.DLog("Exception adding trailer file!")


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
				try: [Log("\t" + writer) for writer in metadata.writers]
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



class xmlnfo(Agent.TV_Shows):
	name = 'XMLnfoImporter(TV Shows)'
	ver = '0.01'
	primary_provider = False
	languages = [Locale.Language.NoLanguage]
	accepts_from = ['com.plexapp.agents.localmedia','com.plexapp.agents.opensubtitles','com.plexapp.agents.podnapisi','com.plexapp.agents.plexthememusic','com.plexapp.agents.subzero']
	contributes_to = ['com.plexapp.agents.thetvdb','com.plexapp.agents.thetvdbdvdorder','com.plexapp.agents.themoviedb']



