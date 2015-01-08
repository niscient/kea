# Various global values


import sys, os
import gbl_helper


if gbl_helper.programDir is not None:   # The program dir is not our starting dir.
	os.chdir(gbl_helper.programDir)
else:
	programDir = os.path.dirname(sys.argv[0])
	if len(programDir) > 0:
		os.chdir(programDir)


programName = 'kea'
musicExts = ('.mp3', '.ogg', '.flac', '.wav')
imageExts = ('.png', '.jpg', '.bmp')

programDir = os.path.dirname(sys.argv[0]) if gbl_helper.programDir is None else gbl_helper.programDir
configExt = '.ini'
# We could use relative paths for these various paths; it's arbitrary.
configPath = os.path.join(programDir, 'kea' + configExt)
dbPath = os.path.join(programDir, 'data.db')
imgDir = os.path.join(programDir, 'img')
interfacesDir = os.path.join(programDir, 'interfaces')
interfacesDirImport = 'interfaces'   # Must match location defined by interfacesDir. TODO maybe auto-generate.
errorPath = os.path.join(programDir, 'err.log')

configBackupSuffix = '_reset'
shortPathLength = 75   # Arbitrary choice, but ideally it should print on one line in an error message box.
websiteAddress = 'http://kea.pylonsoflight.com/'

albumArtFilenames = ['Folder.png', 'folder.png', 'Folder.jpg', 'folder.jpg', 'Album.png', 'album.png', 'Album.jpg', 'album.jpg']

bSupportGlobalWin32Hotkeys = True   # I've left this as an option, just in case leaving it as is might have some unseen performance problems (although I don't see why it would).

restartProgramMessage = 'Restart program to see changes.'

#  ------------------------
# --- Modifiable variables
#  ------------------------

bAppCreated = False

bLibraryChanged = False

bMonitorRemovedDirs = True   # This is an application setting that determines whether the removal and renaming of directories should be monitored. Left as a setting here for the time being in case of unforeseen performance issues.

interfaceName = '' if gbl_helper.interfaceName is None else gbl_helper.interfaceName
interfacePathNoExt = gbl_helper.interfacePathNoExt
interfaceDir = os.path.dirname(interfacePathNoExt) if gbl_helper.interfacePathNoExt is not None else None
saveInterfaceChanges = True

# TODO remove or something
bShowMenuIcons = False

# Current track data. Be sure to reset the row when the table/playlist contents change. An accessor function, ResetCurrentTrackRow(), has been provided to do that, if you prefer to use a function for that."""
currentTrackPath = None
currentTrackTags = None
currentTrackRow = None

def ResetCurrentTrackRow():
	"""Call this or modify the associated global variable directly whenever the table/playlist contents change."""
	global currentTrackRow
	currentTrackRow = None


def BLibraryChanged():
	"""Have the contents of the library changed?"""
	return bLibraryChanged

def SetLibraryChanged():
	"""Mark the library as changed. This can help widgets that might not otherwise check for changes (for example, a treeview that normally only updates a playlist table when a tree branch is clicked if the query has changed) to be on the alert. Make sure you call AcceptCurrentLibrary() at some point after dealing with the library change. (Look in the 'walker' module for a specific callback function approach.)"""
	global bLibraryChanged
	bLibraryChanged = True

def AcceptCurrentLibrary():
	"""Clear the record of any changes made to the library."""
	global bLibraryChanged
	bLibraryChanged = False


bFixGarbageCollection = True
garbageCollectionAnchor = None
def FixGarbageCollection(someWindowOrMainWidgetAttribute):
	"""PyQt4 has problems with garbage collection, particularly when it comes to setting a QSqlQueryModel to a QTableView. You can subvert these problems by affixing some attribute from a main window or main widget to a global value. You can pass such an attribute (or indeed a reference to the main window or widget itself) as an argument here to do this. You won't need to do this if you use SetLibraryChangedCallback(), since it does this kind of thing as a byproduct of its functionality."""
	if bFixGarbageCollection:
		global garbageCollectionAnchor
		garbageCollectionAnchor = someWindowOrMainWidgetAttribute
