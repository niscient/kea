# Library monitoring
#
# Important:
#   This functionality is not yet working, which is why it isn't in use currently.
#
# Notes:
#   Initialize this module by calling StartWatchDirs(), and make sure you call
#  EndWatchDirs() at the end of your program (or the list of directories to watch next
#  time the program runs won't be updated.)
#   The watcher system doesn't always pick up directories that have the same path as
#  other directories, if you're renaming or deleting and recreating directories. To fix
#  this, every time a modification is made inside a directory, every single directory or
#  subdirectory inside the affected directory is quickly checked for existence.
#   Qt will add new directories to its directory list in the order in which they're made.
#
# Bugs:
#   When you delete a directory that's being monitored, Qt is apt to produce the following
#  error message: "QFileSystemWatcher: FindNextChangeNotification failed!! (Access is
#  denied.)" This is an unhelpful error message, and a known bug.


from __future__ import print_function
import sys, os

from util import RequiredImportError

try:
	from PySide import QtCore
	from PySide.QtCore import QFileSystemWatcher
except ImportError:
	try:
		from PyQt4 import QtCore
		from PyQt4.QtCore import QFileSystemWatcher
	except ImportError:
		raise RequiredImportError('No Qt library found.')

import gbl
#from db import SetWatchedDirs   # TODO uncomment, maybe
from walker import LibraryPathFormat


# TODO check all files that are in listdir for a changed dir, and add them to the database if they aren't in there
def DirChanged(dir):
	print('Directory Changed: {}'.format(dir))
	
	watchedDirs = _watcher.directories()
	
	# This is a little inconvenient, but Qt doesn't remove references to renamed or deleted directories, which means that it doesn't pick up on new versions of old-named directories that may come along later.
	if gbl.bMonitorRemovedDirs:
		for watchedDir in watchedDirs:
			if not os.path.isdir(watchedDir):
				_watcher.removePath(watchedDir)
	
	for root, dirs, files in os.walk(dir):
		for name in dirs:
			checkDir = LibraryPathFormat(os.path.join(root, name))
			if checkDir not in watchedDirs:
				print('ADDED', checkDir)
				_watcher.addPath(checkDir)
	print(_watcher.directories(), '\n')

''' # TODO: Remove
def FileChanged(path):
	print('File Changed: {}'.format(path))'''

watchDirs = []

# TODO: make this function and make it work
def StartWatchDirs():
	# TODO: Remove
	rootDirs = []
	#rootDirs = rootDirs[:1]
	
	#watchDirs = []   # TODO uncomment
	
	for rootDir in rootDirs:
		watchDirs.append(rootDir)
		for root, dirs, files in os.walk(rootDir):
			for name in dirs:
				watchDirs.append(os.path.join(root, name))

def EndWatchDirs():
	pass   # TODO


#StartWatchDirs()   # TODO remove
'''
app = QtCore.QCoreApplication(sys.argv)   # TODO: Remove

_watcher = QFileSystemWatcher(watchDirs)
print('dirs', _watcher.directories())
_watcher.directoryChanged.connect(DirChanged)
#_watcher.fileChanged.connect(FileChanged)   # TODO: Remove

sys.exit(app.exec_())   # TODO: Remove'''