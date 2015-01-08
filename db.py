# Database operations
#
# Notes:
#  SQLite is used to keep track of the tags of all the files in the user's music library. Separate
# tables are kept for each File, Artist, Album, and Genre. Another table is used to track
# relationships between albums and artists, and another is used to keep track of the directories
# that comprise the music library.
#  One of the things to note about the database is that it maintains a list of the directories
# that comprise the user's music library. Each time a new dir is added to this list, it is
# checked against the existing list. If it's a subdir of one of the existing dirs, no changes are
# made to the list. If one of the existing dirs is a subdir of it, the old subdir is removed from
# the list and this dir is added instead. If neither of these is the case, the dir is added to the
# list as normal. There's no great reason for all this behavior, it's simply a useful way of
# keeping a concise visual list of the contents of the music library.
#
# To do:
#  Make it so that removing a library dir removes the tags within?


import sys, os, sqlite3
from util import SlashedDir
import gbl
from constants import FAILURE, SUCCESS, PARTIAL_SUCCESS


#  -------------------
# --- Low-Level Setup
#  -------------------


def BTableExists(tableName):
	return c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tableName,)).fetchone() is not None

def CreateTables():
	"""Create the tables for the database, with the unchecked assumption that they're currently nonexistent. No error will be raised if the list of music library dirs already exists. Doesn't commit changes to the database."""
	# Note: For a CREATE TABLE statement, you MUST use INTEGER PRIMARY KEY, not INT PRIMARY KEY, or the rowid will show up as NULL. Note that this only seems to affect tables that have more than one non-rowid field.
	c.execute("CREATE TABLE File (fileid INTEGER PRIMARY KEY, title TEXT, artistid INT, albumid INT, track INT, length TEXT, year INT, genreid INT, path TEXT, FOREIGN KEY(artistid) REFERENCES Artist(artistid), FOREIGN KEY(albumid) REFERENCES Album(albumid), FOREIGN KEY(genreid) REFERENCES Genre(genreid))")
	c.execute("CREATE TABLE Artist (artistid INTEGER PRIMARY KEY, artist TEXT)")
	c.execute("CREATE TABLE Album (albumid INTEGER PRIMARY KEY, album TEXT)")
	c.execute("CREATE TABLE AlbumContainsArtist (albumid INT, artistid INT, PRIMARY KEY(albumid, artistid))")
	c.execute("CREATE TABLE Genre (genreid INTEGER PRIMARY KEY, genre TEXT)")
	
	if not BTableExists('LibraryDirs'):
		c.execute("CREATE TABLE LibraryDirs (dirid INTEGER PRIMARY KEY, dir TEXT)")

def DeleteTable(tableName):
	"""Delete a table, not raising any error on failure. Doesn't commit changes to the database."""
	try:
		c.execute("DROP TABLE " + tableName)
	except sqlite3.OperationalError:   # Table doesn't exist.
		pass

def EmptyTable(tableName):
	"""Delete all entries in a table, not raising any error on failure. Doesn't commit changes to the database."""
	try:
		c.execute("DELETE FROM " + tableName)
	except sqlite3.OperationalError:   # Table doesn't exist.
		pass


#  -----------
# --- Globals
#  -----------

_bCreateTable = not os.path.isfile(gbl.dbPath)

# Store the database connection and cursor.
conn = sqlite3.connect(gbl.dbPath)   # Note that this will create the database file if it doesn't exist.
c = conn.cursor()

if _bCreateTable:
	CreateTables()
	conn.commit()


#  ---------------------
# --- General Functions
#  ---------------------

def ResetDatabaseTags():
	"""Deletes and recreates the tables in the database, except for the list of library dirs, which is not touched (although that will be created if it doesn't currently exist)."""
	# TODO maybe make only drop contents, that might be a little faster (TODO test) despite this being a generally accepted and popular method.
	DeleteTable('File')
	DeleteTable('Artist')
	DeleteTable('Album')
	DeleteTable('AlbumContainsArtist')
	DeleteTable('Genre')
	CreateTables()
	conn.commit()

def GetEntry(entries, id):
	"""Utility function. Given a list of entries which have the primary key as the first item of each entry, return the entry which has a matching primary key (ID) or return None."""
	for entry in entries:
		if entry[0] == id:
			return entry
	return None


#  ----------------
# --- Library Dirs
#  ----------------

def LibraryDirFormat(dir):
	"""Returns an absolute, normalized path with forwards slashes only and no final path separator at the end (unless the dir is a drive)."""
	return os.path.abspath(os.path.realpath(dir)).replace('\\', '/')

def ResetLibraryDirs():
	"""Resets the list of stored music library dirs. Doesn't affect tag data."""
	DeleteTable('LibraryDirs')
	c.execute("CREATE TABLE LibraryDirs (dirid INTEGER PRIMARY KEY, dir TEXT)")
	conn.commit()

def RemoveLibraryDirFromList(dir):
	"""Remove a dir from the music library dir list."""
	dir = LibraryDirFormat(dir)
	c.execute("DELETE FROM LibraryDirs WHERE dir=?", (dir,))
	conn.commit()

def AddLibraryDirToList(dir, bCheckCovered=True):
	"""Adds a dir to the list of music library dirs. Pass bCheckCovered=False if you've already gotten a False result from BLibraryDirCovered() for this dir. After calling this function, any existing dir that the new dir covers may be removed from the library dir list, so you should obtain a new copy of that table. Returns FAILURE if the dir was not added, SUCCESS if it was a totally unique new directory, and PARTIAL_SUCCESS if it subsumed an old library dir."""
	dir = LibraryDirFormat(dir)
	
	if bCheckCovered:
		if BLibraryDirCovered(dir):
			return FAILURE   # Dir is already covered by existing library dirs.
	
	# Remove any existing dir that's covered by the new dir.
	bClashes = False
	slashedDir = SlashedDir(dir)
	libDirs = GetLibraryDirs()
	for libDir in libDirs:
		if SlashedDir(libDir).startswith(slashedDir):
			c.execute("DELETE FROM LibraryDirs WHERE dir=?", (libDir,))
			bClashes = True
	
	c.execute("INSERT INTO LibraryDirs VALUES (NULL, ?)", (dir,))
	conn.commit()
	if bClashes:
		return PARTIAL_SUCCESS
	return SUCCESS

def GetLibraryDirs():
	"""Get a list of existing music library dirs."""
	return [dir for dirid, dir in c.execute("SELECT * FROM LibraryDirs").fetchall()]

def BIsLibraryDir(dir):
	"""Returns whether a potential music library dir is already in the list of music library dirs. This does not test if it's a subdir of one of those dirs."""
	dir = LibraryDirFormat(dir)
	return dir in GetLibraryDirs()

def BLibraryDirCovered(dir):
	"""Returns whether a potential music library dir is included by an existing, larger library dir."""
	dir = LibraryDirFormat(dir)
	slashedDir = SlashedDir(dir)
	libDirs = GetLibraryDirs()
	for libDir in libDirs:
		if slashedDir.startswith(SlashedDir(libDir)):
			return True
	return False
