# kea-specific utility functions
#
# Notes:
#  For the main file, go to main.py.
#   QApplication instances are stored locally because it seems to be a really bad idea to store
#  them globally on PyQt4 (PySide is fine with it). It can lead to all kinds of bizarre problems
#  when you try to close your application.


import sys, os, traceback, time, datetime

try:
	import configparser
except:
	import ConfigParser as configparser

from qt import *
from util import LogicError, RequiredImportError
import gbl
#from gbl import EnsureProgramDir
import db
from config import GetConfigFile, GetStandardWindowSetup, WriteConfigFile
from walker import LibraryPathFormat
from hotkeys import GlobalWin32HotkeysApplication, DeleteGlobalHotkeys, DeleteGlobalWin32Hotkeys


#  -----------
# --- Setup
#  -----------

def MakeKeaWindow(mainWindowClass, *mainWindowClassInitArgs, **kw_args):
	"""Set up a kea main window. Should be run by most interfaces, although it's easier to use it through MakeKeaWindow() (and even better to use it through RunStdInterface() or RunShapedInterface()) to automate the window geometry. Generally, pass in the name of the StdMainWindow or ShapedMainWindow class or subclass to use, followed by the arguments to that class's __init__() function. One of these arguments will be the name of your main widget class (the main class that defines your interface). You can explicitly set the keyword arg 'bRun' to True to make an application wrapper to run the main window in."""
	# Get keyword args.
	bRun = kw_args.get('bRun', True)
	
	if bRun:
		if gbl.bSupportGlobalWin32Hotkeys:
			# Create an application which supports Win32 global hotkeys.
			app = GlobalWin32HotkeysApplication([])
		else:
			app = QApplication([])
		app.setApplicationName(gbl.programName)   # Phonon might print a warning later if we don't do this.
		# TODO remove or make work
		if not gbl.bShowMenuIcons:
			app.setAttribute(Qt.AA_DontShowIconsInMenus)
	
	window = mainWindowClass(*mainWindowClassInitArgs)
	#window.show()   # TODO remove.
	
	if bRun:
		app.exec_()
		
		db.conn.commit()
		db.conn.close()


def MakeStdArgsKeaWindow(mainWindowClass, mainWidgetClass, configFileOrFileAttribute, **kw_args):
	"""Runs MakeKeaWindow() indirectly, with the assumption that the main window class uses standard kea main window argument order. Handles window geometry automatically when __file__ or a config file object is passed in by the calling interface module. This function should be run by most interfaces, unless you use RunStdInterface or RunShapedInterface (which is a better idea).
	This function makes some heavy assumptions about the order of arguments in your main window class, which is why you should keep them standard (See StdMainWindow and ShapedMainWindow).
	Pass in the name of the StdMainWindow or ShapedMainWindow class to use, followed by the name of your main widget class (the main class that defines your interface). As the next argument, you can either pass in a config file object or the __file__ attribute of your interface module.
	
	Keyword args:
	bWindowUsesConfigFile: Important: Use this to determine whether to send the config file as an argument to the main window's __init__() function. Set this to False if using a base window class, which doesn't deal with config files directly. If you forget to send this when using a base window class, it will result in the wrong arguments being sent to the function. True by default.
	shapedImgPath: Set this if using a shaped main window.
	bRun: Determines whether to make an application wrapper to run the main window in. True by default.
	"""
	# Get keyword args. (The reason I'm parsing them this way is in case I later add *args-supplying functionality to this function.)
	bWindowUsesConfigFile = kw_args.get('bWindowUsesConfigFile', True)
	shapedImgPath = kw_args.get('shapedImgPath', None)
	bRun = kw_args.get('bRun', True)
	
	bShapedWindow = shapedImgPath is not None
	
	bOpenedConfigFile = False
	
	if isinstance(configFileOrFileAttribute, configparser.ConfigParser):
		configFile = configFileOrFileAttribute
	else:
		configFile = GetConfigFile(configFileOrFileAttribute)
		bOpenedConfigFile = True
	
	values = GetStandardWindowSetup(configFile, bShapedWindow)
	
	if bOpenedConfigFile:
		configFile.close()
	
	if bShapedWindow:
		x, y = [int(var) for var in values[:2]]
		if bWindowUsesConfigFile:
			MakeKeaWindow(mainWindowClass, shapedImgPath, x, y, mainWidgetClass, configFile, bRun=bRun)
		else:
			MakeKeaWindow(mainWindowClass, shapedImgPath, x, y, mainWidgetClass, bRun=bRun)
	else:
		x, y, w, h = [int(var) for var in values[:4]]
		bMaximized = values[4].lower() == 'true'
		if bWindowUsesConfigFile:
			MakeKeaWindow(mainWindowClass, x, y, w, h, bMaximized, mainWidgetClass, configFile, bRun=bRun)
		else:
			MakeKeaWindow(mainWindowClass, x, y, w, h, bMaximized, mainWidgetClass, bRun=bRun)


# TODO maybe make these Run function use configFileOrFileAttribute instead of configFile, like MakeStdArgsKeaWindow does. Or maybe not.

def RunStdInterface(parentClass, mainWidgetClass, configFile, bWindowUsesConfigFile=True):
	"""The standard code used to run a non-shaped interface. Pass in the main window class, main widget class, and the interface's config file object. Set 'bWindowUsesConfigFile' to False if using a window base class."""
	try:
		#StartWatchDirs()   # TODO
		MakeStdArgsKeaWindow(parentClass, mainWidgetClass, configFile, bWindowUsesConfigFile=bWindowUsesConfigFile)
		if gbl.saveInterfaceChanges:   # In case the user is trying to reset the interface config file to the backup file, we don't want to overwrite the config file.
			WriteConfigFile(configFile)
	finally:
		pass #EndWatchDirs()   # TODO
		DeleteGlobalHotkeys()
		DeleteGlobalWin32Hotkeys()

def RunShapedInterface(parentClass, shapedImgPath, mainWidgetClass, configFile, bWindowUsesConfigFile=True):
	"""The standard code used to run a shaped interface. Pass in the main window class, main widget class, and the interface's config file object. Set 'bWindowUsesConfigFile' to False if using a window base class."""
	try:
		#StartWatchDirs()   # TODO
		MakeStdArgsKeaWindow(parentClass, mainWidgetClass, configFile, bWindowUsesConfigFile=bWindowUsesConfigFile, shapedImgPath=shapedImgPath)
		if gbl.saveInterfaceChanges:   # In case the user is trying to reset the interface config file to the backup file, we don't want to overwrite the config file.
			WriteConfigFile(configFile)
	finally:
		pass #EndWatchDirs()   # TODO
		DeleteGlobalHotkeys()
		DeleteGlobalWin32Hotkeys()


#  ------------
# --- Messages
#  ------------

def LogTraceback():
	"""Log the most recent exception(s) to the error log."""
	traceback.print_exc(file=sys.stdout)
	print()
	timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y %I:%M:%S %p')
	with open(gbl.errorPath, 'a') as errorFile:
		errorFile.write(timestamp)
		errorFile.write(':\n\n')
		traceback.print_exc(file=errorFile)
		errorFile.write('\n')
LogError = LogTraceback

def ShowError(*args, **kw_args):
	"""Show an error message box, and optionally log the error. Assumes that an exception has just been caught (give the argument bLogTraceback=False if not). You can pass in the keyword args 'sep', 'bLogTraceback', and 'bIgnoreTracebackError'."""
	# Get keyword args.
	sep = kw_args.get('sep', ' ')
	bLogTraceback = kw_args.get('bLogTraceback', True)
	bIgnoreTracebackError = kw_args.get('bIgnoreTracebackError', True)
	
	try:
		strArgs = [str(e) for e in args]
	except UnicodeEncodeError as error:
		try:
			strArgs = [unicode(e) for e in strArgs]   # See if the problem was Python 2's non-Unicode str class.
		except NameError:   # No Python 2 Unicode class exists.
			raise error
	message = sep.join(strArgs)
	
	# Note: Testing if QtGui.qApp is None doesn't work with PyQt4 (it does with PySide), so I've done this instead.
	if gbl.bAppCreated == False:
		app = QApplication([])   # Create an application shell to be able to show error messages.
	
	ShowQtMessage(QMessageBox.Critical, gbl.programName, message, QMessageBox.Ok)
	
	if bLogTraceback:
		try:
			LogTraceback()
		except AttributeError:   # No exception traceback was found.
			if not bIgnoreTracebackError:
				raise

# TODO make line break seps work? they don't for some reason in QErrorMessage.
def ShowBlockableError(parent, *args, **kw_args):
	"""Show an error message box, and optionally log the error. This message box allows you to block further error messages with the same text. Qt requires a parent element to exist for this function to work. Assumes that an exception has just been caught (give the argument bLogTraceback=False if not). You can pass in the keyword args 'sep', 'bLogTraceback', and 'bIgnoreTracebackError'."""
	if parent is None:
		return
	
	# Get keyword args.
	sep = kw_args.get('sep', ' ')
	bLogTraceback = kw_args.get('bLogTraceback', True)
	bIgnoreTracebackError = kw_args.get('bIgnoreTracebackError', True)
	
	try:
		strArgs = [str(e) for e in args]
	except UnicodeEncodeError as error:
		try:
			strArgs = [unicode(e) for e in strArgs]   # See if the problem was Python 2's non-Unicode str class.
		except NameError:   # No Python 2 Unicode class exists.
			raise error
	message = sep.join(strArgs)
	
	if gbl.bAppCreated == False:
		app = QApplication([])   # Create an application shell to be able to show error messages.
	
	errorMsg = QErrorMessage(parent)
	# TODO maybe try fiddling with the color more; I can't seem to change the "second background color".
	#palette = errorMsg.palette()
	#palette.setColor(errorMsg.backgroundRole(), Qt.blue)
	#palette.setColor(errorMsg.foregroundRole(), Qt.blue)
	#errorMsg.setPalette(palette)
	errorMsg.showMessage(message)
	
	if bLogTraceback:
		try:
			LogTraceback()
		except AttributeError:   # No exception traceback was found.
			if not bIgnoreTracebackError:
				raise

# TODO center in window?
def ShowQtMessage(*args):
	"""Shortcut method of creating an official Qt message box."""
	msgBox = QMessageBox(*args)
	msgBox.exec_()

def ShowMessage(*args, **kw_args):
	sep = kw_args.get('sep', ' ')
	try:
		strArgs = [str(e) for e in args]
	except UnicodeEncodeError as error:
		try:
			strArgs = [unicode(e) for e in strArgs]   # See if the problem was Python 2's non-Unicode str class.
		except NameError:   # No Python 2 Unicode class exists.
			raise error
	message = sep.join(strArgs)
	ShowQtMessage(QMessageBox.NoIcon, gbl.programName, message, QMessageBox.Ok)

def ShowWarning(*args, **kw_args):
	sep = kw_args.get('sep', ' ')
	try:
		strArgs = [str(e) for e in args]
	except UnicodeEncodeError as error:
		try:
			strArgs = [unicode(e) for e in strArgs]   # See if the problem was Python 2's non-Unicode str class.
		except NameError:   # No Python 2 Unicode class exists.
			raise error
	message = sep.join(strArgs)
	ShowQtMessage(QMessageBox.Warning, gbl.programName, message, QMessageBox.Ok)

def ShowRestartChangesMessage():
	ShowQtMessage(QMessageBox.NoIcon, gbl.programName, gbl.restartProgramMessage, QMessageBox.Ok)


#  --------------
# --- Interfaces
#  --------------

def GetImgDir():
	return os.path.join(gbl.interfaceDir, 'img')

def CreateStdHotkeys(widget, playerManager, configFile=None, bUseGlobalHotkeys=None):
	"""Create a series of standard kea shortcuts. Pass in a window/widget, a class using the StdPlayerManager interface, and a config file (if you want to see if global hotkeys are supported by the interface) as arguments. You can also provide a bUseGlobalHotkeys override."""
	if bUseGlobalHotkeys is None:
		if configFile is None:
			bUseGlobalHotkeys = False
		else:
			try:
				bUseGlobalHotkeys = configFile.get('Program', 'bUseGlobalHotkeys').lower() == 'true'
			except configparser.NoOptionError:
				bUseGlobalHotkeys = False
	
	#bUseGlobalHotkeys = True   # TODO remove
	if bUseGlobalHotkeys:
		if not CreateGlobalWin32Hotkey(VK_NUMPAD4, None, playerManager.Prev):
			QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_4), widget, playerManager.Prev)
		if not CreateGlobalWin32Hotkey(VK_NUMPAD5, None, playerManager.PlayRandom):
			QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_5), widget, playerManager.PlayRandom)
		if not CreateGlobalWin32Hotkey(VK_NUMPAD6, None, playerManager.Next):
			QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_6), widget, playerManager.Next)
		if not CreateGlobalWin32Hotkey(VK_NUMPAD8, None, playerManager.TogglePaused):
			QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_8), widget, playerManager.TogglePaused)
		if not CreateGlobalWin32Hotkey(VK_NUMPAD2, None, playerManager.Replay):
			QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_2), widget, playerManager.Replay)
	else:
		QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_4), widget, playerManager.Prev)
		QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_6), widget, playerManager.Next)
		QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_5), widget, playerManager.PlayRandom)
		QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_8), widget, playerManager.TogglePaused)
		QShortcut(QKeySequence(Qt.KeypadModifier + Qt.Key_2), widget, playerManager.Replay)
	
	QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left), widget, playerManager.Prev)
	QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right), widget, playerManager.Next)
	QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Up), widget, playerManager.TogglePaused)
	QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Down), widget, playerManager.PlayRandom)
	QShortcut(QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_Left), widget, playerManager.Replay)
	
	QShortcut(QKeySequence('Space'), widget, playerManager.TogglePaused)


#  -------------
# --- Databases
#  -------------

def GetTableDB():
	db = QSqlDatabase.addDatabase('QSQLITE')
	db.setDatabaseName(gbl.dbPath)
	db.open()
	return db


#  -----------
# --- Queries
#  -----------

def GetStandardTrackQuery():
	return 'SELECT track, title, path FROM File, Artist, Album, Genre WHERE File.artistid == Artist.artistid AND File.albumid == Album.albumid AND File.genreid == Genre.genreid ORDER BY artist COLLATE NOCASE ASC, album COLLATE NOCASE ASC'

def StripOrderBy(query):
	"""Strips the query string of the 'ORDER BY' string and everything after it. Leaves any whitespace before 'ORDER BY'. Only works if the string uses the fully capitalized version of 'ORDER BY.'"""
	pos = query.find('ORDER BY')
	if pos != -1:
		return query[:pos]
	return query


# TODO maybe make more flexible
def InsertSearchIntoQuery(query, clause, word, clauseSuffix=u"{}'"):
	"""Insert a case-insensitive search into a query.
	Note that the query must have an ORDER BY clause and a WHERE clause, and that an existing query, if it queries some column, 'column', will always use the "AND column='...'" format (using = or LIKE), indicating the existence of previous WHERE checks as well).
	You must pass in AND at the start of 'clause', and a single quote at the end, as in "AND column='".
	'clauseSuffix' must be a Unicode string for Python 2 compatibility. It is used for string formatting. Note the SQL wildcard character, %.
	The point is, the query and arguments must be formatted very specially.
	"""
	
	if not query.find('WHERE'):
		raise LogicError('Invalid query (no WHERE clause)')
	orderByPos = query.find('ORDER BY')
	if orderByPos == -1:
		raise LogicError('Invalid query (no ORDER BY clause)')
	
	word = word.replace("'", "''")   # Escape the quote character.
	
	clausePos = query.find(clause)
	if clausePos != -1:
		endClausePos = query.find("'", clausePos + len(clause))
		while endClausePos != -1:
			if len(query) > endClausePos + 1 and query[endClausePos + 1] == "'":   # We found an escaped quote, ignore it.
				endClausePos = query.find("'", endClausePos + 2)
			else:
				break
		if endClausePos == -1:
			raise LogicError('Invalid query (unmatched quote in clause.)')
		
		query = query[:clausePos] + clause + clauseSuffix.format(word) + query[endClausePos + 1:]
	else:
		query = query[:orderByPos] + clause + clauseSuffix.format(word) + u' ' + query[orderByPos:]
	
	return query

def InsertDirSearchIntoQuery(query, dir):
	dir = LibraryPathFormat(dir)
	if not dir.endswith('/'):   # It might be a drive, in which case it'll have a slash at the end.
		dir += '/'
	return InsertSearchIntoQuery(query, "AND path LIKE '", dir, u"{}%'")

def InsertWordSearchIntoQuery(query, word):
	return InsertSearchIntoQuery(query, "AND path LIKE '", word, u"%{}%'")

def InsertArtistSearchIntoQuery(query, artist):
	return InsertSearchIntoQuery(query, "AND artist='", artist)

def InsertAlbumSearchIntoQuery(query, album):
	return InsertSearchIntoQuery(query, "AND album='", album)



#  ----------------------
# --- Interface Elements
#  ----------------------

class DrawPixmap:
	def __init__(self, pixmapOrImgPath, x, y):
		if isinstance(pixmapOrImgPath, QPixmap):
			self.pixmap = pixmapOrImgPath
		else:
			self.pixmap = QPixmap(pixmapOrImgPath)
		self.width = self.pixmap.width()
		self.height = self.pixmap.height()
		self.x = x
		self.y = y


def GetAlbumArtFromDir(dir):
	for filename in gbl.albumArtFilenames:
		path = os.path.join(dir, filename)
		if os.path.isfile(path):
			return path
	return None


def GetHoverButton(parent, imgPath, hoverImgPath, bFocusable=False):
	"""Get a QPushButton that can be used as a hover button."""
	# URLs in style sheets are very picky about path separator characters.
	imgPath = imgPath.replace('\\', '/')
	hoverImgPath = hoverImgPath.replace('\\', '/')
	
	pixmap = QPixmap(imgPath)
	button = QPushButton(parent=parent)
	button.resize(pixmap.rect().size())
	button.setStyleSheet('QPushButton {{ background-color: transparent; border-image: url("{}"); background-repeat: none; border: none; }} QPushButton:hover {{ border-image: url("{}"); }}'.format(imgPath, hoverImgPath))
	if not bFocusable:
		button.setFocusPolicy(Qt.NoFocus)
	
	return button

def GetHoverButtonData(parent, imgPath, hoverImgPath, bFocusable=False):
	"""Get some data that can be used for a QPushButton hover button. Specifically, get the button, its normal icon, and a hover icon. You can use the returned data to set the button's icons to the hovered or un-hovered versions later."""
	pixmap = QPixmap(imgPath)
	icon = QIcon(pixmap)
	hoverIcon = QIcon(QPixmap(hoverImgPath))
	
	button = QPushButton(parent=parent)
	button.resize(pixmap.rect().size())
	button.setIcon(icon)
	button.setIconSize(pixmap.rect().size())
	button.setStyleSheet('background: transparent; border: none;')
	if not bFocusable:
		button.setFocusPolicy(Qt.NoFocus)
	
	return button, icon, hoverIcon

def GetHoverButtonIconData(imgPath, hoverImgPath):
	"""Get some data that can be used for a QPushButton hover button. Specifically, get the normal icon and a hover icon. You can use the returned data to set a button's icons to the hovered or un-hovered versions later."""
	pixmap = QPixmap(imgPath)
	icon = QIcon(pixmap)
	hoverIcon = QIcon(QPixmap(hoverImgPath))
	
	return icon, hoverIcon

