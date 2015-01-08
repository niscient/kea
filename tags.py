# Music file tags
#
# Notes:
#  Currently, mutagen is the only supported main audio library. hsaudiotag support has
# been disabled because it has faulty ID3v2.4 support. Unfortunately, mutagen doesn't work
# on Python 3 yet.
#  If a track has, say, an artist of None, a value to that effect will actuall be made in
# the database's Artist table, with an ID to match. This will allow us to actually use
# that as a valid artist primary key when making queries.
#  Both mutagen and hsaudiotag have problems getting correct file lengths from WAV files,
# so I use a custom solution. mutagen won't even read WAV files at all.


from __future__ import print_function
import os
from struct import unpack_from
from util import RequiredImportError, PathNotExistError, BPython2, SQ

# This is commented out until hsaudiotag fixes its ID3v2.4 problems. For now, mutagen is the
# only library supported. Since mutagen is broken on Python 3, this means that Python 2 is the
# only language supported.
# TODO: Reenable if hsaudiotag is ever updated.
'''
try:
	import hsaudiotag   # Arbitrarily, try hsaudiotag before mutagen.
	from hsaudiotag import auto
except ImportError:
	if Python2():   # As of this writing, mutagen has only partial Python 3 support. TODO: Keep track of this.
		import mutagen
	else:
		raise RequiredImportError('No music tag library found.')   # Neither library is available.
'''
import mutagen
#from hsaudiotag import auto


def PrintableAudioLength(seconds):
	return '{}:{num:02d}'.format(int(seconds / 60), num=int(seconds) % 60)

def GetFileTagsMutagen(path):
	"""Uses Mutagen to get music file tags. Must return the same output as GetFileTagsHsaudiotag. Returns the list [title, artist, album, track, length, year, genre, path]."""
	if not os.path.exists(path):
		raise PathNotExistError('File doesn\'t exist:', SQ(path))
	
	audio = mutagen.File(path, easy=True)
	
	title = audio.get('title', None)
	if title is not None and len(title[0]) > 0:   # Note: On Python 2 I got one rare situation where the title was indeed a blank string, which is why I test for it here, but it's usually None if no title is found. (And on Python 3 this rare example gave None.)
		title = title[0]
	else:
		title = os.path.basename(path)   # Note loading the filename instead of using a blank title.
	artist = audio.get('artist', None)
	if artist is not None:
		artist = artist[0]
	album = audio.get('album', None)
	if album is not None:
		album = album[0]
	track = audio.get('tracknumber', None)
	if track is not None:
		track = track[0]
		if '/' in track:
			track = track[:track.find('/')]
		try:
			track = int(track)
		except ValueError:
			track = None
	year = audio.get('date', None)
	if year is not None:
		try:
			year = int(year[0])
		except ValueError:
			year = None
	genre = audio.get('genre', None)
	if genre is not None:
		genre = genre[0]
	
	return [title, artist, album, track, PrintableAudioLength(audio.info.length), year, genre, path]
'''
def GetFileTagsHsaudiotag(path):
	"""Uses hsaudiotag to get music file tags. Must return the same output as GetFileTagsMutagen. (Note: hsaudiotag ignores tracknumbers of 0 due to inbuilt limitations.) Returns the list [title, artist, album, track, length, year, genre, path]."""
	if not os.path.exists(path):
		raise PathNotExistError('File doesn\'t exist:', SQ(path))
	
	audio = auto.File(path)
	
	title = audio.title if audio.title != '' else os.path.basename(path)   # Note loading the filename instead of using a blank title.
	artist = audio.artist if audio.artist != '' else None
	album = audio.album if audio.album != '' else None
	track = audio.track if audio.track != 0 and audio.track != '' else None   # hsaudiotag limitation; blanks or invalid values always appear as 0. The '' test is a courtesy.
	try:
		year = int(audio.year) if audio.year != '' else None
	except ValueError:
		year = None
	genre = audio.genre if audio.genre != '' else None
	
	return [title, artist, album, track, PrintableAudioLength(audio.duration), year, genre, path]
'''
def GetWAVFileTags(path):
	if not os.path.exists(path):
		raise PathNotExistError('File doesn\'t exist:', SQ(path))
	
	title = os.path.basename(path)   # Note loading the filename instead of using a blank title.
	artist = album = track = year = genre = None
	
	return [title, artist, album, track, GetWAVFileLength(path), year, genre, path]

def GetFileLengthMutagen(path):
	"""Uses Mutagen to get music file length. Must return the same output as GetFileLengthHsaudiotag."""
	if not os.path.exists(path):
		raise PathNotExistError('File doesn\'t exist:', SQ(path))
	audio = mutagen.File(path, easy=True)
	PrintableAudioLength(audio.info.length)
'''
def GetFileLengthHsaudiotag(path):
	"""Uses hsaudiotag to get music file length. Must return the same output as GetFileLengthMutagen."""
	if not os.path.exists(path):
		raise PathNotExistError('File doesn\'t exist:', SQ(path))
	audio = auto.File(path)
	return PrintableAudioLength(audio.duration)
'''
def GetWAVFileLength(path):
	with open(path, 'r') as file:
		file.seek(28)   # The WAV ByteRate is located at the 28th byte.
		byteRateData = file.read(4)
		
		# Convert the value from a string (stored in little endian, in fact) into an int.
		''' # Alternative to unpack_from. TODO: Remove, I guess.
		byteRate = 0
		for i in range(4):
			byteRate = byteRate + ord(byteRateData[i]) * pow(256, i)
		'''
		byteRate = unpack_from('<l', byteRateData)[0]
		
		fileSize = os.path.getsize(path)
		if byteRate == 0:   # This is probably an error on the part of the file, but we'll accept it.
			seconds = 0
		else:
			seconds = (fileSize - 44) / byteRate   # 44 is the byte position of the actual sound data.
		return PrintableAudioLength(seconds)


# TODO: Reenable if hsaudiotag is ever updated to support ID3v2.4.
'''
# Import audio library and determine which versions of certain functions to use based on that.
try:
	hsaudiotag   # Has hsaudiotag been imported?
	GetFileTags = GetFileTagsHsaudiotag
	GetFileLength = GetFileLengthHsaudiotag
except ImportError:
	mutagen   # Has mutagen been imported?
	GetFileTags = GetFileTagsMutagen
	GetFileLength = GetFileLengthMutagen
'''
#GetFileTags = GetFileTagsMutagen
#GetFileLength = GetFileLengthHsaudiotag

def GetFileTags(path):
	if os.path.splitext(path)[1].lower() == '.wav':
		return GetWAVFileTags(path)
	else:
		return GetFileTagsMutagen(path)

def GetFileLength(path):
	if os.path.splitext(path)[1].lower() == '.wav':
		return GetWAVFileLength(path)
	else:
		return GetFileTagsMutagen(path)
