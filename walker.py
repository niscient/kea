# Directory walking
#
# Notes:
#  Provides various functions for walking directories and adding the tag data of the files they
# contain to the database.
#  We stick with one type of path separator only in internally-stored file paths, to keep things
# simple and searchable. Library dirs, by contrast, are stored using the user's operating system's
# preferred path separator.
#
# To do:
#  Real-time music library monitoring, as a later (post-Independent Study) task. This will be
#  preferable to manually clicking a Refresh button to recognize changes to the files or directory
#  structures.


from __future__ import print_function
import os

from util import SepException, SQ, SlashedDir
from constants import *
import db
from db import LibraryDirFormat, BIsLibraryDir, BLibraryDirCovered, AddLibraryDirToList, RemoveLibraryDirFromList
import gbl
from gbl import SetLibraryChanged
from tags import GetFileTagsMutagen, GetWAVFileTags, GetFileLength


# Globals
_libChangedCallback = None
_libChangedCallbackArgs = None
_libChangedCallbackKwArgs = None


class LibraryDirError(SepException):
	pass


def LibraryPathFormat(dir):
	"""Returns an absolute, normalized path with forwards slashes only and no final slash at the end (unless the dir is a drive)."""
	return os.path.abspath(os.path.realpath(dir)).replace('\\', '/')

def GetMusicFiles(dir):
	dir = os.path.abspath(os.path.realpath(dir))
	paths = []
	for root, dirs, filenames in os.walk(dir, topdown=True):
		for name in filenames:
			ext = os.path.splitext(name)[1].lower()
			if ext in gbl.musicExts:
				paths.append(os.path.join(root, name).replace('\\', '/'))
	return paths

def GetMusicFilesInRootOnly(dir):
	dir = os.path.abspath(os.path.realpath(dir))
	paths = []
	for filename in os.listdir(dir):
		ext = os.path.splitext(filename)[1].lower()
		if ext in gbl.musicExts:
			paths.append(os.path.join(dir, filename).replace('\\', '/'))
	return paths


def AddLibraryDirToDatabase(dir):
	"""Load the contents of a new music library dir into the database. Only succeeds in a situation where no existing library dir includes this dir. (This means that the application shouldn't be allowed to remove subdirs from the library, or this function won't be able to add them back.) Note that, if the passed-in dir doesn't clash with an existing library dir, then we won't check whether the files in the new dir already exist in the database. This should not present a problem as long as the library dir list is kept up-to-date. Returns a bool indicating whether the dir was added or not."""
	result = AddLibraryDirToList(dir)
	if result == FAILURE:   # This dir is already covered by an existing library dir.
		return False
	bCheckFileClashes = result == PARTIAL_SUCCESS   # We subsumed an existing library dir, so some of our files might already be in the database.
	
	paths = GetMusicFiles(dir)
	return _AddFilesToDatabase(paths, bCheckFileClashes=bCheckFileClashes, bAddNothingIfAnyClash=False)

def _AddFilesToDatabase(paths, bCheckFileClashes=True, bAddNothingIfAnyClash=False):
	"""Add tags from a list of files to the database. It's inefficient to call this function for files one by one, so only do that (using a tuple with one element in it) if you must. Returns a list of any files that failed to be added. Although this function is designed with later extensibility in mind (thus the arguments that can be set), currently it is only intended to be used with official library dirs, which is why this function is marked as private."""
	# Note that we're going to insert the artists, albums, etc., in the order in which they're retrieved by the dir-walking functionality. This might come in handy later.
	# This function generates its own new primary keys for new artists, albums, and genres.
	# Note that even a track with, say, no artist, actually has an artist ID, automatically set to a special row in the Artist table. This will help simplify things later when we make queries. We can always assume that each File has a valid artistid, etc.
	# Possibly TODO: I could program Python 2 to replace every instance of a call to items() in this function with viewitems(), but there's little performance gain to be had from that.
	
	# Note that for artists, albums, and genres, we'll create and store IDs (primary keys) as well as the rest of the values. This is so that we can have ready access to those IDs, so we can connect albums to artists easily as well as easily turn tag strings into IDs.
	files = []
	artists = {}
	albums = {}
	genres = {}
	
	oldArtistsList = db.c.execute("SELECT * FROM Artist").fetchall()
	oldArtists = dict((id, artist) for id, artist in oldArtistsList)
	nextArtistID = oldArtistsList[-1][0] + 1 if len(oldArtistsList) > 0 else 1
	
	oldAlbumsList = db.c.execute("SELECT * FROM Album").fetchall()
	oldAlbums = dict((id, album) for id, album in oldAlbumsList)
	nextAlbumID = oldAlbumsList[-1][0] + 1 if len(oldAlbumsList) > 0 else 1
	
	oldGenresList = db.c.execute("SELECT * FROM Genre").fetchall()
	oldGenres = dict((id, genre) for id, genre in oldGenresList)
	nextGenreID = oldGenresList[-1][0] + 1 if len(oldGenresList) > 0 else 1
	
	albumContainsArtistList = []
	oldAlbumContainsArtistList = db.c.execute("SELECT * FROM AlbumContainsArtist").fetchall()
	#print("OLD", oldAlbumContainsArtistList)   # TODO REMOVE
	
	failed = []
	
	if bCheckFileClashes and bAddNothingIfAnyClash:   # TODO possibly: Remove bCheckFileClashes check. Or not, it's based on a subjective interpretation of how arguments work.
		for path in paths:
			if db.c.execute("SELECT COUNT(*) FROM File WHERE path=?", (path,)).fetchone()[0] > 0:
				failed.append(path)
		if len(failed) > 0:
			return failed
	
	for path in paths:
		if bCheckFileClashes:
			if db.c.execute("SELECT COUNT(*) FROM File WHERE path=?", (path,)).fetchone()[0] > 0:
				failed.append(path)
				continue
		
		# TODO remove this block
		'''if os.path.splitext(path)[1].lower() == '.wav':   # WAV files don't officially support tags, so we'll handle them differently.
			# Note loading the filename instead of using a blank title.
			tags = [os.path.basename(path), None, None, None, GetFileLength(path), None, None, path]
			files.append(tags)
			continue'''
		if os.path.splitext(path)[1].lower() == '.wav':
			tags = GetWAVFileTags(path)   # mutagen and hsaudiotag currently have problems with WAV files.
		else:
			tags = GetFileTagsMutagen(path)
		artistID = albumID = genreID = None
		
		# Obtain the artist ID and store a new row in the artists dict if necessary.
		artistName = tags[DB_ARTIST]
		for k, v in oldArtists.items():
			if v == artistName:
				artistID = k
				break
		if artistID is None:
			for k, v in artists.items():
				if v == artistName:
					artistID = k
					break
			if artistID is None:
				artistID = nextArtistID
				artists[artistID] = artistName
				nextArtistID += 1
		tags[DB_ARTIST] = artistID
		
		# Do the same for the album.
		albumName = tags[DB_ALBUM]
		for k, v in oldAlbums.items():
			if v == albumName:
				albumID = k
				break
		if albumID is None:
			for k, v in albums.items():
				if v == albumName:
					albumID = k
					break
			if albumID is None:
				albumID = nextAlbumID
				albums[albumID] = albumName
				nextAlbumID += 1
		tags[DB_ALBUM] = albumID
		
		# Do the same for the genre.
		genreName = tags[DB_GENRE]
		for k, v in oldGenres.items():
			if v == genreName:
				genreID = k
				break
		if genreID is None:
			for k, v in genres.items():
				if v == genreName:
					genreID = k
					break
			if genreID is None:
				genreID = nextGenreID
				genres[genreID] = genreName
				nextGenreID += 1
		tags[DB_GENRE] = genreID
		
		files.append(tags)
		
		albumContainsArtistData = (albumID, artistID)
		if albumContainsArtistData not in oldAlbumContainsArtistList and albumContainsArtistData not in albumContainsArtistList:
			albumContainsArtistList.append(albumContainsArtistData)
			#print("NEW", (albumName, artistName), albumContainsArtistData)   # TODO REMOVE
	
	# TODO remove
	#print('OLDART', oldArtists)
	#print('NEWART', artists)
	
	# Note that for the data we insert from dictionaries, insertion order doesn't matter since we've precomputed the primary keys to use.
	if len(files) > 0:
		db.c.executemany("INSERT INTO File VALUES (NULL, ?,?,?,?,?,?,?,?)", files)
	if len(artists) > 0:
		db.c.executemany("INSERT INTO Artist VALUES (?, ?)", artists.items())
	if len(albums) > 0:
		db.c.executemany("INSERT INTO Album VALUES (?, ?)", albums.items())
	if len(genres) > 0:
		db.c.executemany("INSERT INTO Genre VALUES (?, ?)", genres.items())
	if len(albumContainsArtistList) > 0:
		db.c.executemany("INSERT INTO AlbumContainsArtist VALUES (?, ?)", albumContainsArtistList)
	
	db.conn.commit()
	SetLibraryChanged()
	RunLibraryChangedCallback()
	
	return failed


def RescanLibraryDirOrSubdir(dir, bRescanTags, bUpdateAll=True, bCheckDir=True):
	"""Rescan the contents of a library dir or subdir. Clashes are expected, so all files are tested. If 'bUpdateAll' is set, Artists, Albums, and Genres of deleted files are tested for rationalization of continued existence."""
	dir = LibraryDirFormat(dir)
	if bCheckDir and not BLibraryDirCovered(dir):
		raise LibraryDirError('Invalid library dir or subdir:', SQ(dir))
	
	if bRescanTags:
		RemoveLibraryDirOrSubdirFromDatabase(dir, bRemoveDirFromList=False, bUpdateAll=bUpdateAll, bCheckDir=False)
	
	paths = GetMusicFiles(dir)
	return _AddFilesToDatabase(paths, bCheckFileClashes=not bRescanTags, bAddNothingIfAnyClash=False)


# TODO test further
def RemoveLibraryDirOrSubdirFromDatabase(dir, bRemoveDirFromList=True, bUpdateAll=True, bCheckDir=True):
	"""Remove File entries of all files in the dir from the database. Other tables are unaffected. This should only be called on an existing library dir. If 'bRemoveDirFromList' is set to False, the dir, if it's a library dir, will not be removed from the list of library dirs. If 'bUpdateAll' is set, Artists, Albums, and Genres of deleted files are pruned."""
	dir = LibraryDirFormat(dir)
	if bCheckDir and not BLibraryDirCovered(dir):
		raise LibraryDirError('Invalid library dir or subdir:', SQ(dir))
	
	slashedDir = SlashedDir(dir)
	
	if bUpdateAll:
		values = db.c.execute("SELECT artistid, albumid, genreid FROM File WHERE path LIKE ?", (slashedDir + '%',)).fetchall()
	
	db.c.execute("DELETE FROM File WHERE path LIKE ?", (slashedDir + '%',))
	
	if bUpdateAll:
		# Use values retrieved earlier to test for deletion.
		artistIDs = set([e[0] for e in values])
		albumIDs = set([e[1] for e in values])
		genreIDs = set([e[2] for e in values])
		for artistID in artistIDs:
			if artistID is not None:
				if db.c.execute("SELECT COUNT(*) FROM File WHERE artistid=?", (artistID,)).fetchone()[0] == 0:
					db.c.execute("DELETE FROM Artist WHERE artistid=?", (artistID,))
					db.c.execute("DELETE FROM AlbumContainsArtist WHERE artistid=?", (artistID,))
		for albumID in albumIDs:
			if albumID is not None:
				if db.c.execute("SELECT COUNT(*) FROM File WHERE albumid=?", (albumID,)).fetchone()[0] == 0:
					db.c.execute("DELETE FROM Album WHERE albumid=?", (albumID,))
					db.c.execute("DELETE FROM AlbumContainsArtist WHERE albumid=?", (albumID,))
		for genreID in genreIDs:
			if genreID is not None:
				if db.c.execute("SELECT COUNT(*) FROM File WHERE genreid=?", (genreID,)).fetchone()[0] == 0:
					db.c.execute("DELETE FROM Genre WHERE genreid=?", (genreID,))
	
	db.conn.commit()
	
	if bRemoveDirFromList and BIsLibraryDir(dir):
		RemoveLibraryDirFromList(dir)
	
	# TODO remove the dir from the watched dirs list, once i implement that
	
	SetLibraryChanged()
	RunLibraryChangedCallback()


def RemoveFileFromDatabase(path, bUpdateAll=True, libChangedCallbackArgs=None):
	"""Removes a file from the database. If 'bUpdateAll' is set, Artists, Albums, and Genres of deleted files are pruned. Optionally, you can pass a set of arguments to pass to the library changed callback function. This is because that function will be called, but it's common not to need to refresh/redraw certain GUI elements just because a file was deleted. You can alert the callback function to this fact."""
	path = LibraryPathFormat(path)
	
	if bUpdateAll:
		values = db.c.execute("SELECT artistid, albumid, genreid FROM File WHERE path=?", (path,)).fetchone()
		if values is not None:   # No match in database.
			artistID, albumID, genreID = values   # Note that never-set values are None, as usual.
		else:
			artistID = albumID = genreID = None
	
	db.c.execute("DELETE FROM File WHERE path=?", (path,))
	
	if bUpdateAll:
		# Reuse variables created earlier.
		if artistID is not None:
			if db.c.execute("SELECT COUNT(*) FROM File WHERE artistid=?", (artistID,)).fetchone()[0] == 0:
				db.c.execute("DELETE FROM Artist WHERE artistid=?", (artistID,))
				db.c.execute("DELETE FROM AlbumContainsArtist WHERE artistid=?", (artistID,))
		if albumID is not None:
			if db.c.execute("SELECT COUNT(*) FROM File WHERE albumid=?", (albumID,)).fetchone()[0] == 0:
				db.c.execute("DELETE FROM Album WHERE albumid=?", (albumID,))
				db.c.execute("DELETE FROM AlbumContainsArtist WHERE albumid=?", (albumID,))
		if genreID is not None:
			if db.c.execute("SELECT COUNT(*) FROM File WHERE genreid=?", (genreID,)).fetchone()[0] == 0:
				db.c.execute("DELETE FROM Genre WHERE genreid=?", (genreID,))
	
	db.conn.commit()
	SetLibraryChanged()
	if libChangedCallbackArgs is not None:
		RunLibraryChangedCallback(*libChangedCallbackArgs)
	else:
		RunLibraryChangedCallback()


def BFileInDatabase(path):
	"""Checks whether a file path is already stored in the database."""
	path = LibraryPathFormat(path)
	return db.c.execute("SELECT COUNT(*) FROM File WHERE path=?", (path,)).fetchone()[0] > 0


def PrintFileTableLookup(selectQueryResults):
	"""A programmer's maintenance function, designed to print the fetchall() output of a File table SELECT query. It prints some values as normal, but turns the foreign keys into the appropriate strings."""
	artists = dict((id, artist) for id, artist in db.c.execute("SELECT * FROM Artist").fetchall())
	albums = dict((id, album) for id, album in db.c.execute("SELECT * FROM Album").fetchall())
	genres = dict((id, genre) for id, genre in db.c.execute("SELECT * FROM Genre").fetchall())
	
	for tags in selectQueryResults:
		print(tags[0], tags[1], ' ', artists[tags[2]], ' ', albums[tags[3]], tags[4], tags[5], tags[6], genres[tags[7]], end='\n\n')


def SetLibraryChangedCallback(func, *args, **kw_args):
	"""Set a callback function to be run when the contents of the library change, and arguments to pass this function. You should probably call AcceptCurrentLibrary() from inside the function."""
	global _libChangedCallback, _libChangedCallbackArgs, _libChangedCallbackKwArgs
	_libChangedCallback = func
	if len(args) > 0:
		_libChangedCallbackArgs = args
	_libChangedCallbackKwArgs = kw_args

def RunLibraryChangedCallback(*args, **kw_args):
	"""Run the callback function that was set to run when the library changes. You can supply custom arguments or use the initially set ones."""
	if _libChangedCallback is not None:
		if len(args) > 0 or len(kw_args) > 0:
			_libChangedCallback(*args, **kw_args)
		else:
			if _libChangedCallbackArgs is not None:
				_libChangedCallback(*_libChangedCallbackArgs, **_libChangedCallbackKwArgs)
			else:
				_libChangedCallback(**_libChangedCallbackKwArgs)