# rectangular
# Created by Rains Jordan
# Last updated 12/4/14
#
# Non-standard shortcuts:
#   Ctrl+Home, Ctrl+End: Move to start/end of playlist column view, if the window size is
#  too small.
#
# Notes:
#   This is a simple demonstration of a sample kea interface, using a standard windowed interface
#  with a track table and a directory tree.
#
# Implementation notes:
#   This file is more of a custom-rigged interface than the Shaped interface, with a custom table
#  and track pane which are highly dependent on each other, making free use of each other's
#  resources.
#   This file demonstrates a main widget-heavy solution, where most of the code is based around
#  the main widget. Even the main window code takes place there, using custom events. (The
#  alternative would be to use a StdMainWidget subclass like CommonStdMainWidget.)
#   There are a few commented-out blocks of code in this file where I explain how we would do
#  things if using StdMainWindowBase instead of StdMainWindow.
#
# To do:
#  


#!/usr/bin/env python

from __future__ import absolute_import, print_function
if __name__ == '__main__':
	import direct_test_enabler   # Make the interface runnable directly, for testing purposes. This should be done before most of the other imports.

from std_interface_imports import *
from std_main_window import StdMainWindow
from dir_system_model import DirSystemModel, GetBRemoveSingleTreeRootNode
from std_player_manager import StdPlayerManager
from std_progress_bar import StdProgressBar
from simple_track_query_table import SimpleTrackQueryTable


parentClass = StdMainWindow
config = GetConfigFile()
imgDir = GetImgDir()

# A lot of literals are used for positioning purposes in this file, but here are a few ones that are worth naming.
SEARCH_AREA_WIDTH = 203   # Approximate width of the relevant part of the search area decoration image. The + 1 is cosmetic.
SEARCH_AREA_HEIGHT = 112
SEARCH_AREA_RIGHT_BUFFER = 84   # The amount of pixels needed to push the search area right decoration to the correct position.
SEARCH_AREA_LEFT_WIDTH = 118
SEARCH_AREA_MIDDLE_WIDTH = 1   # The width of the scalable middle section.
ALBUM_ART_SIZE = 192
VOLUME_BAR_TOP = 22
VOLUME_BAR_HEIGHT = 59
PROGRESS_BAR_LEFT = 300
PROGRESS_BAR_RIGHT = 20


class CustomSplitter(QSplitter):
	"""A custom QSplitter designed to work with my main widget."""
	
	def __init__(self, orientation, parent):
		self.parent = parent
		# For some reason, if the parent is supplied, Qt acts weird and doesn't display the tree right. So we won't pass the parent argument in.
		super(CustomSplitter, self).__init__(orientation)
	
	def createHandle(self):
		return CustomSplitterHandle(Qt.Horizontal, self)

class CustomSplitterHandle(QSplitterHandle):
	def __init__(self, orientation, parent):
		self.parent = parent
		super(CustomSplitterHandle, self).__init__(orientation, parent)
	
	def mouseMoveEvent(self, event):
		self.parent.parent.tree.resize(self.parent.parent.treeFrame.width(), self.parent.parent.treeFrame.height() - SEARCH_AREA_HEIGHT)
		
		super(CustomSplitterHandle, self).mouseMoveEvent(event)
		
		if self.parent.sizes()[0] < SEARCH_AREA_WIDTH:   # Test the width of the first element in the splitter.
			self.parent.parent.searchDecorationLeft.hide()
			self.parent.parent.searchDecorationMiddle.hide()
			self.parent.parent.searchDecorationRight.hide()
			self.parent.parent.searchText.hide()
			self.parent.parent.searchBox.hide()
		else:
			self.parent.parent.searchDecorationMiddle.setScaledContents(True)
			self.parent.parent.searchDecorationMiddle.resize(self.parent.parent.treeFrame.width() - SEARCH_AREA_WIDTH + SEARCH_AREA_MIDDLE_WIDTH, SEARCH_AREA_HEIGHT)
			self.parent.parent.searchDecorationMiddle.move(SEARCH_AREA_LEFT_WIDTH, self.parent.parent.height() - SEARCH_AREA_HEIGHT)
			
			self.parent.parent.searchDecorationRight.move(self.parent.parent.treeFrame.width() - SEARCH_AREA_RIGHT_BUFFER, self.parent.parent.height() - SEARCH_AREA_HEIGHT)
			
			self.parent.parent.searchDecorationLeft.show()
			self.parent.parent.searchDecorationMiddle.show()
			self.parent.parent.searchDecorationRight.show()
			self.parent.parent.searchText.show()
			self.parent.parent.searchBox.show()



# Note: This class has custom mouse events, but I've left them as external event handlers, so to speak, in the main widget because they're so inextricably linked with the widget's activities.
class LibraryTreeView(QTreeView):    
	def edit(self, index, trigger, event):
		if trigger == QtGui.QAbstractItemView.DoubleClicked:
			return False
		return QtGui.QTreeView.edit(self, index, trigger, event)


class MainWidget(QWidget):
	def __init__(self, parent):   # The main widget should take the main window as its first argument.
		super(MainWidget, self).__init__(parent)
		self.parent = parent
		
		
		##--- Tree
		
		self.dirSystemModel = DirSystemModel(self, config)
		
		self.treeFrame = QFrame()
		self.treeFrame.setStyleSheet('background-color: #e2e2e2;')
		self.treeFrame.setMinimumSize(SEARCH_AREA_WIDTH, 0)   # For search area.
		self.treeFrame.resizeEvent = self.resizeTreeFrameEvent
		
		self.tree = LibraryTreeView(self.treeFrame)
		self.tree.setModel(self.dirSystemModel)
		
		if len(GetLibraryDirs()) == 1:
			if not GetBRemoveSingleTreeRootNode(config):
				# Expand the first node of the tree.
				firstIndex = self.tree.model().index(0, 0, QModelIndex())
				self.tree.setExpanded(firstIndex, True)
		
		self.tree.setStyleSheet('QTreeView { border: 0px; }')
		self.tree.setHeaderHidden(True)
		self.tree.keyPressEvent = self.keyPressTreeEvent
		self.tree.mousePressEvent = self.mousePressTreeEvent
		self.tree.mouseDoubleClickEvent = self.mouseDoubleClickTreeEvent
		
		treeScrollbarStyle = '''
		/* Style #1 */
		/*QScrollBar:vertical { width: 14px; background-color: white; color: black; }*/
		
		/* Style #2 */
		QScrollBar:vertical { width: 8px; }
		QScrollBar:handle:vertical { min-height: 5px; border-top: 8px solid #e2e2e2; border-bottom: 8px solid #e2e2e2; border-left: 2px solid #e2e2e2; border-right: 2px solid #e2e2e2; background: qlineargradient(x1: 0, y1: 0.8, x2: 1, y2: 0.8, stop: 0 darkgray, stop: 1 black); }
		
		QScrollBar:sub-page, QScrollBar:add-page { background-color: #e2e2e2; }
		'''
		self.tree.verticalScrollBar().setStyleSheet(treeScrollbarStyle)
		
		
		##--- The rest of the widget
		
		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		
		hSplitter = CustomSplitter(Qt.Horizontal, self)
		
		self.table = MainTable(self)
		
		self.trackFrame = TrackFrame(self)
		
		vSplitter = QSplitter(Qt.Vertical)
		vSplitter.addWidget(self.table)
		vSplitter.addWidget(self.trackFrame)
		
		# Make the track window not resize when the overall window size is changed.
		vSplitter.setStretchFactor(0, 1)
		vSplitter.setStretchFactor(1, 0)
		
		vSplitter.setStyleSheet('QSplitter { background: #e6e6e6; height: 1px; }')
		
		hSplitter.addWidget(self.treeFrame)
		hSplitter.addWidget(vSplitter)
		
		hSplitter.setObjectName('mainHSplitter')
		hSplitter.setStyleSheet('QSplitter#mainHSplitter { width: 2px; } QSplitter#mainHSplitter::handle { background-color: #8a8a8a; border-left: 1px solid #9b9b9b; }')
		
		# It doesn't matter much what the second argument (or the first argument, exactly) here is, as long as it's big enough to handle the rest of the widget.
		hSplitter.setSizes([SEARCH_AREA_WIDTH, parent.width()])
		
		hbox.addWidget(hSplitter)
		self.setLayout(hbox)
		
		# Note: We'll set the positions of these things in the resize event.
		
		self.searchDecorationLeft = QLabel(self)
		pixmap = QPixmap(os.path.join(imgDir, 'search_area_left.png'))
		self.searchDecorationLeft.setPixmap(pixmap)
		self.searchDecorationLeft.resize(pixmap.rect().size())
		#self.searchDecorationLeft.setStyleSheet('background-color: rgba(0,0,0,0%)')   # TODO: Remove.
		
		self.searchDecorationMiddle = QLabel(self)
		pixmap = QPixmap(os.path.join(imgDir, 'search_area_middle.png'))
		self.searchDecorationMiddle.setPixmap(pixmap)
		self.searchDecorationMiddle.resize(pixmap.rect().size())
		#self.searchDecorationMiddle.setStyleSheet('background-color: rgba(0,0,0,0%)')   # TODO: Remove.
		
		self.searchDecorationRight = QLabel(self)
		pixmap = QPixmap(os.path.join(imgDir, 'search_area_right.png'))
		self.searchDecorationRight.setPixmap(pixmap)
		self.searchDecorationRight.resize(pixmap.rect().size())
		#self.searchDecorationRight.setStyleSheet('background-color: rgba(0,0,0,0%)')   # TODO: Remove, I guess.
		
		self.searchText = QLabel('Search:', parent=self)
		self.searchText.setFont(QFont(config.get('General', 'fontName'), int(config.get('General', 'fontSize')) - 1))
		self.searchText.setAttribute(Qt.WA_TranslucentBackground)
		
		self.searchBox = QLineEdit(self)
		self.searchBox.setStyleSheet('background-color: #e2e2e2; border-top: 1px solid #adadad; border-bottom: 1px solid #adadad; border-left: 2px solid #adadad; border-right: 2px solid #adadad;')
		self.searchBox.resize(self.searchBox.width(), self.searchBox.height() - 5)   # TODO customize based on OS or something?
		
		
		##--- Add action(s) to main toolbar
		
		self.parent.mainMenu.settingsMenu.addSeparator()
		removeSingleTreeNodeAction = QAction('&Remove single tree node?', self)
		removeSingleTreeNodeAction.setCheckable(True)
		removeSingleTreeNodeAction.setChecked(GetBRemoveSingleTreeRootNode(config))
		removeSingleTreeNodeAction.triggered.connect(self.ToggleRemoveSingleTreeNode)
		self.parent.mainMenu.settingsMenu.addAction(removeSingleTreeNodeAction)
		
		
		# These won't catch the first events, from before the main widget is created, but it doesn't matter.
		# NOTE: We would use this if using StdMainWindowBase.
		#self.parent.moveEvent = self.moveWindowEvent
		#self.parent.resizeEvent = self.resizeWindowEvent
		
		self.searchBox.keyPressEvent = self.keyPressSearchBoxEvent
		self.searchBox.textChanged.connect(self.SearchTextChanged)
		self.searchText.mousePressEvent = self.mousePressSearchTextEvent
		
		SetLibraryChangedCallback(self.LibraryChangedCallback)
		
		CreateStdHotkeys(self, self.trackFrame.playerManager, config)
		
		QShortcut(QKeySequence('Ctrl+T'), self, self.OnFocusTree)
		QShortcut(QKeySequence('Ctrl+F'), self, self.OnFocusSearch)
		QShortcut(QKeySequence('Ctrl+R'), self, self.OnFocusResults)
		
		# TODO delete
		#self.parent.installEventFilter(self)
		
		#from std_main_window import AboutDialog
		#self.tempDialog = AboutDialog(parent)
	
	def LibraryChangedCallback(self, bRedrawTree=True):
		if bRedrawTree:
			self.tree.model().Reload()
		self.table.ReloadQuery()
		AcceptCurrentLibrary()
	
	def OnFocusTree(self):
		self.tree.setFocus()
	
	def OnFocusSearch(self):
		self.searchBox.setFocus()
	
	def OnFocusResults(self):
		# TODO highlight row here? not always done already. maybe not.
		self.table.setFocus()
	
	def LoadDirContents(self, dir):
		self.table.ModifyQuery(InsertDirSearchIntoQuery, dir)
	
	def LaunchSearch(self):
		word = self.searchBox.text()
		if len(word) > 0:
			self.table.ModifyQuery(InsertWordSearchIntoQuery, word)
	
	def resizeEvent(self, event):
		self.searchDecorationLeft.move(0, self.height() - SEARCH_AREA_HEIGHT)
		
		self.searchDecorationMiddle.setScaledContents(True)
		self.searchDecorationMiddle.resize(self.treeFrame.width() - SEARCH_AREA_WIDTH + SEARCH_AREA_MIDDLE_WIDTH, SEARCH_AREA_HEIGHT)
		self.searchDecorationMiddle.move(SEARCH_AREA_LEFT_WIDTH, self.height() - SEARCH_AREA_HEIGHT)
		
		self.searchDecorationRight.move(self.treeFrame.width() - SEARCH_AREA_RIGHT_BUFFER, self.height() - SEARCH_AREA_HEIGHT)
		self.searchText.move(28, self.height() - 91)
		self.searchBox.move(16, self.height() - 64)
		
		super(MainWidget, self).resizeEvent(event)
	
	'''
	# NOTE: We would use this if using StdMainWindowBase.
	def moveWindowEvent(self, event):
		bMaximized = self.parent.windowState() & Qt.WindowMaximized
		if not bMaximized:
			config.set('Program', 'x', str(event.pos().x()))
			config.set('Program', 'y', str(event.pos().y()))
		super(parentClass, self.parent).moveEvent(event)
	
	def resizeWindowEvent(self, event):
		if self.parent.windowState() & Qt.WindowMaximized:
			config.set('Program', 'bMaximized', str(True))
		else:
			config.set('Program', 'bMaximized', str(False))
			config.set('Program', 'width', str(event.size().width()))
			config.set('Program', 'height', str(event.size().height()))
		super(parentClass, self.parent).resizeEvent(event)
	'''
	
	def ToggleRemoveSingleTreeNode(self, bChecked):
		config.set('Program', 'bRemoveSingleTreeRootNode', str(bChecked))
		ShowRestartChangesMessage()
	
	def resizeTreeFrameEvent(self, event):
		self.tree.resize(self.treeFrame.width(), self.treeFrame.height() - SEARCH_AREA_HEIGHT)
	
	def keyPressTreeEvent(self, event):
		if event.key() == Qt.Key_Right:
			index = self.tree.currentIndex()
			if not self.tree.isExpanded(index):
				self.dirSystemModel.AllowExpandLayer(index)
		elif event.key() == Qt.Key_Return:
			index = self.tree.currentIndex()
			dir = self.dirSystemModel.dir(index)
			if dir is not None:
				self.LoadDirContents(dir)
		super(LibraryTreeView, self.tree).keyPressEvent(event)
	
	def mousePressTreeEvent(self, event):
		"""Select a tree branch."""
		# Note: Doesn't check to see if indexes apply to actual items, but that seems to be harmless.
		if event.buttons() & Qt.LeftButton:
			index = self.tree.indexAt(event.pos())
			dir = self.dirSystemModel.dir(index)
			if dir is not None:   # It will be None if we, say, clicked on some random spot in the tree view that didn't have an actual item there.
				self.LoadDirContents(dir)
		super(LibraryTreeView, self.tree).mousePressEvent(event)
	
	def mouseDoubleClickTreeEvent(self, event):
		"""Open/close a tree branch."""
		# Note: Doesn't check to see if indexes apply to actual items, but that seems to be harmless.
		if event.buttons() & Qt.LeftButton:
			index = self.tree.indexAt(event.pos())
			# TODO: I have no idea why the boolean values used in here work. They should be the opposite.
			if self.tree.isExpanded(index):
				self.tree.setExpanded(index, True)
			else:
				self.dirSystemModel.AllowExpandLayer(index)
				self.tree.setExpanded(index, False)
		super(LibraryTreeView, self.tree).mouseDoubleClickEvent(event)
	
	def keyPressSearchBoxEvent(self, event):
		if event.key() == Qt.Key_Return:
			self.LaunchSearch()
		else:
			QLineEdit.keyPressEvent(self.searchBox, event)
	
	def SearchTextChanged(self, text):
		font = self.searchText.font()
		bNonBlank = len(text) != 0
		font.setItalic(bNonBlank)
		font.setUnderline(bNonBlank)
		if bNonBlank:
			self.searchText.setStyleSheet('color: #111d79;')
		else:
			self.searchText.setStyleSheet('color: black;')
		self.searchText.setFont(font)
	
	def mousePressSearchTextEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			self.LaunchSearch()


class MainTable(SimpleTrackQueryTable):
	def __init__(self, parent):
		super(MainTable, self).__init__(parent, highlightColor='#cfc7d6', bAlternatingRowColors=True)
		
		# Set up various important details.
		self.columnHeaders = {}
		self.columnVisualIndexes = {}
		self.sortedHeader = None
		self.sorted = None
		
		# Parent overrides
		self.bHidePathColumn = False   # We always need a path column so the data will be accessible, but it may not be visible.
		
		self.LoadConfigFile()
		
		self.horizontalHeader().setStretchLastSection(False)   # TODO: keep?
		self.horizontalHeader().show()   # Parent override
		self.horizontalHeader().setStyleSheet('font-size: 12px; font-weight: bold; color: {};'.format(config.get('General', 'headerColor')))
		self.verticalHeader().setClickable(True)
		
		self.horizontalHeader().setMovable(True)
		self.horizontalHeader().sectionClicked.connect(self.HeaderClicked)
		self.horizontalHeader().sectionMoved.connect(self.ColumnMoved)
		self.horizontalHeader().sectionResized.connect(self.ColumnResized)
		
		self.libChangedCallbackArgs = (False,)   # Allows us not to redraw the tree when mere file(s) are deleted.
		
		self.SetItemCallback(self.ChooseTrack)
	
	def ChooseTrack(self, path, row):
		gbl.currentTrackRow = row
		self.parent.trackFrame.PlayFile(path)
	
	def LoadConfigFile(self):
		columnSizes = {}
		fieldLookup = {'title':'title AS Title', 'artist':'artist AS Artist', 'album':'album AS Album', 'track':"track AS '#'", 'length':'length AS Length', 'year':'year AS Year', 'genre':'genre AS Genre', 'path':'path AS Path'}
		self.query = 'SELECT '
		
		i = 0
		while True:
			if config.has_option('Table', 'c' + str(i)):
				value = config.get('Table', 'c' + str(i))
				if value not in fieldLookup:
					raise ConfigValueError(value)
				
				self.columnHeaders[i] = value
				self.columnVisualIndexes[i] = i
				columnSizes[i] = int(config.get('Table', 'c' + str(i) + 'width'))
				self.query += fieldLookup[value] + ', '
				
				if value == 'path':
					self.dataColumn = i   # Set the path column.
			else:
				break
			i += 1
		
		# The path needs to be in our results somewhere, so generate and hide it if necessary.
		if self.dataColumn is None:
			self.query += 'path, '
			self.dataColumn = i
			self.bHidePathColumn = True
		
		# The initial query behavior. Note that we create an extra column as padding.
		self.query += "NULL AS '' FROM File, Artist, Album, Genre WHERE File.artistid == Artist.artistid AND File.albumid == Album.albumid AND File.genreid == Genre.genreid ORDER BY "
		
		# The initial sorting behavior.
		self.query += 'artist COLLATE NOCASE ASC, album COLLATE NOCASE ASC'
		self.sortedHeader = 'artist'
		self.sorted = SORTED_ASC
		
		self.setFont(QFont(config.get('General', 'fontName'), int(config.get('General', 'fontSize'))))
		
		self._LoadQuery(self.query, bLoadEvenIfSameQuery=True)
		
		for i in range(len(columnSizes)):
			self.setColumnWidth(i, columnSizes[i])
		
		self.setColumnHidden(self.model.columnCount() - 1, True)
	
	def HeaderClicked(self, index):
		"""Sorts the contents of the table when a header is clicked."""
		if index >= len(self.columnHeaders):   # Clicked on the empty padding column.
			return
		#print('CLICKED', index, self.columnHeaders[index])   # TODO remove
		header = self.columnHeaders[index]
		if self.sortedHeader == header and self.sorted == SORTED_ASC:
			if header == 'artist':
				self.query = StripOrderBy(self.query) + ' ORDER BY artist COLLATE NOCASE DESC, album COLLATE NOCASE ASC'
			else:
				self.query = StripOrderBy(self.query) + ' ORDER BY ' + header + ' COLLATE NOCASE DESC'
			self.sorted = SORTED_DESC
		else:
			if header == 'artist':
				self.query = StripOrderBy(self.query) + ' ORDER BY artist COLLATE NOCASE ASC, album COLLATE NOCASE ASC'
			else:
				self.query = StripOrderBy(self.query) + ' ORDER BY ' + header + ' COLLATE NOCASE ASC'
			self.sorted = SORTED_ASC
		self.sortedHeader = header
		self._LoadQuery(self.query, bLoadEvenIfSameQuery=True)
		
		#print(self.query)   # TODO remove
	
	def ColumnMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
		# If we either moved the empty padding column or moved something past that column, it'll screw up our visual index arithmetic, so undo it.
		if logicalIndex >= len(self.columnHeaders) or newVisualIndex >= len(self.columnHeaders):
			self.horizontalHeader().sectionMoved.disconnect(self.ColumnMoved)
			self.horizontalHeader().moveSection(newVisualIndex, oldVisualIndex)
			self.horizontalHeader().sectionMoved.connect(self.ColumnMoved)
			return
		
		movedWidth = config.get('Table', 'c' + str(oldVisualIndex) + 'width')   # Store this for later.
		
		# Move other columns' visual indexes to fit with the newly moved column. We'll go in order, either up or down depending on which direction the column moved in, so that we only ever overwrite options we've already dealt with.
		# Note that we don't need to "wipe out" the old options when their index numbers change, as they're guaranteed to be overwritten by new values by the end of the loop anyway.
		
		if oldVisualIndex < newVisualIndex:
			# Move columns left one by one, starting with the leftmost.
			for i in sorted(self.columnVisualIndexes, key=self.columnVisualIndexes.get):   # Scan columns in ascending order by visual index.
				if i != logicalIndex:   # Don't move our original column.
					visualIndex = self.columnVisualIndexes[i]
					if visualIndex > oldVisualIndex and visualIndex <= newVisualIndex:
						self.columnVisualIndexes[i] -= 1
						width = config.get('Table', 'c' + str(visualIndex) + 'width')
						config.set('Table', 'c' + str(visualIndex - 1) + 'width', str(width))
						config.set('Table', 'c' + str(visualIndex - 1), self.columnHeaders[i])
		else:
			# Move columns right one by one, starting with the rightmost.
			for i in sorted(self.columnVisualIndexes, key=self.columnVisualIndexes.get, reverse=True):   # Scan columns in descending order by visual index.
				if i != logicalIndex:   # Don't move our original column.
					visualIndex = self.columnVisualIndexes[i]
					if visualIndex < oldVisualIndex and visualIndex >= newVisualIndex:
						self.columnVisualIndexes[i] += 1
						width = config.get('Table', 'c' + str(visualIndex) + 'width')
						config.set('Table', 'c' + str(visualIndex + 1) + 'width', str(width))
						config.set('Table', 'c' + str(visualIndex + 1), self.columnHeaders[i])
		
		self.columnVisualIndexes[logicalIndex] = newVisualIndex
		config.set('Table', 'c' + str(newVisualIndex), self.columnHeaders[logicalIndex])
		config.set('Table', 'c' + str(newVisualIndex) + 'width', movedWidth)
	
	def ColumnResized(self, logicalIndex, oldSize, newSize):
		if logicalIndex >= len(self.columnHeaders):   # Resized the empty padding column, either directly or indirectly (by fiddling with the window, or other columns).
			return
		
		visualIndex = self.columnVisualIndexes[logicalIndex]   # We need to use the visual index because that's what's used in the config file; our logical indexes never change while the program is running.
		config.set('Table', 'c' + str(visualIndex) + 'width', str(newSize))


class TrackFrame(QFrame):
	def __init__(self, parent):
		super(TrackFrame, self).__init__(parent)
		self.parent = parent
		self.resize(1, 216)   # The width doesn't matter.
		self.setStyleSheet('QFrame { background-color: #d8d8d8; }')
		
		self.playerManager = StdPlayerManager(self, trackTable=self.parent.table)
		
		# Note: We set the size/position of many of these things in the resize event.
		
		
		##--- Album art decoration
		
		self.albumArtDecoration = QLabel(self)
		self.albumArtDecoration.setPixmap(QPixmap(os.path.join(imgDir, 'album_art_area.png')))
		self.albumArtDecoration.setAttribute(Qt.WA_TranslucentBackground)
		
		
		##--- Album art
		
		self.albumArt = QLabel(self)
		self.albumArt.setAttribute(Qt.WA_TranslucentBackground)
		self.albumArt.move(12, 9)
		
		
		##--- Textual info
		
		fontName = config.get('General', 'paneFontName')
		fontSize = int(config.get('General', 'paneFontSize'))
		font = QFont(fontName, fontSize)
		
		maxSizeUsed = fontSize + 5   # The maximum font size that will be used here. It's okay to overestimate this, so I have. Truth is, we could use a huge value with no problem.
		maxFontMetrics = QFontMetrics(QFont(fontName, maxSizeUsed))
		self.maxFontHeight = maxFontMetrics.height()   # It doesn't matter really if this is too big.
		
		self.artistText = QLabel(self)
		self.artistText.setFont(font)
		self.artistText.setAttribute(Qt.WA_TranslucentBackground)
		self.artistText.move(242, 30)
		
		self.albumText = QLabel(self)
		self.albumText.setFont(font)
		self.albumText.setAttribute(Qt.WA_TranslucentBackground)
		self.albumText.move(242, 58)
		
		self.trackText = QLabel(self)
		self.trackText.setFont(QFont(fontName, fontSize + 2))
		self.trackText.setAttribute(Qt.WA_TranslucentBackground)
		self.trackText.setTextFormat(Qt.RichText)   # Possibly unnecessary.
		self.trackText.move(242, 86)
		
		self.genreText = QLabel(self)
		self.genreText.setFont(QFont(fontName, fontSize - 2))
		self.genreText.setAttribute(Qt.WA_TranslucentBackground)
		self.genreText.move(250, 118)
		
		
		##--- Buttons
		
		self.playerManager.AddPrevButton(os.path.join(imgDir, 'prev_button.png'), os.path.join(imgDir, 'prev_button_hover.png'), 0, 0)
		self.playerManager.AddPauseButton(os.path.join(imgDir, 'play_button.png'), os.path.join(imgDir, 'play_button_hover.png'), os.path.join(imgDir, 'pause_button.png'), os.path.join(imgDir, 'pause_button_hover.png'), 0, 0)
		self.playerManager.AddNextButton(os.path.join(imgDir, 'next_button.png'), os.path.join(imgDir, 'next_button_hover.png'), 0, 0)
		
		
		##--- Progress bar
		
		self.progressBar = StdProgressBar(self, 0, 0, 0, 0, self.playerManager.player)
		
		
		##--- Volume bar
		
		self.volumeBar = VolumeBar(self, self.playerManager)
		
		
		QShortcut(QKeySequence('Ctrl+Alt+Up'), self, self.IncreaseVolume)
		QShortcut(QKeySequence('Ctrl+Alt+Down'), self, self.DecreaseVolume)
	
	def resizeEvent(self, event):
		self.albumArtDecoration.move(0, self.height() - 172)
		
		# This is all sort of unnecessary since we could pick some unreasonably large number at the start and stick with it, but let's do this anyway.
		maxTextWidth = self.width()   # Doesn't matter if this is too big, really.
		self.artistText.resize(maxTextWidth, self.maxFontHeight)
		self.albumText.resize(maxTextWidth, self.maxFontHeight)
		self.trackText.resize(maxTextWidth, self.maxFontHeight)
		self.genreText.resize(maxTextWidth, self.maxFontHeight)
		
		self.playerManager.prevButton.move(self.width() * .62, 13)
		self.playerManager.pauseButton.move(self.width() * .62 + 38, 13)
		self.playerManager.nextButton.move(self.width() * .62 + 68, 13)
		
		progressBarX = self.width() / 2
		progressBarWidth = self.width() / 2 - PROGRESS_BAR_RIGHT
		if progressBarX > PROGRESS_BAR_LEFT:
			progressBarWidth += progressBarX - PROGRESS_BAR_LEFT
			progressBarX = PROGRESS_BAR_LEFT
		self.progressBar.resize(progressBarWidth, 50)
		self.progressBar.move(progressBarX, 130)
		
		self.volumeBar.volumeBarFill.move(self.width() - 39, self.volumeBar.volumeBarFill.y())
		self.volumeBar.volumeBarShape.move(self.width() - 39, VOLUME_BAR_TOP)
		super(TrackFrame, self).resizeEvent(event)
	
	def PlayFile(self, path):
		self.playerManager.PlayFile(path)
		
		# Set values for each field.
		
		tags = gbl.currentTrackTags
		fontName = config.get('General', 'paneFontName')
		fontSize = int(config.get('General', 'paneFontSize'))
		font = QFont(fontName, fontSize)
		
		oldDir = os.path.dirname(gbl.currentTrackPath) if gbl.currentTrackPath is not None else None
		dir = os.path.dirname(tags[DB_PATH])
		if dir != oldDir:
			albumArtPath = GetAlbumArtFromDir(dir)
			if albumArtPath is None:
				self.albumArt.hide()
			else:
				albumArtPixmap = QPixmap(albumArtPath)
				self.albumArt.setPixmap(albumArtPixmap.scaled(ALBUM_ART_SIZE, ALBUM_ART_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
				self.albumArt.resize(ALBUM_ART_SIZE, ALBUM_ART_SIZE)   # Note: This is only necessary when setting the album art later instead of at the start.
				self.albumArt.show()
		
		if tags[DB_ARTIST] is None:
			self.artistText.setText('')
		else:
			self.artistText.setText(tags[DB_ARTIST])
		
		if tags[DB_ALBUM] is None:
			self.albumText.setText('')
		else:
			self.albumText.setText(tags[DB_ALBUM])
		
		trackStr = ''
		if tags[DB_TRACK] is not None:
			trackStr += "<span style='font-size: {}pt;'>#{}: </span>".format(fontSize, str(tags[DB_TRACK]))
		if tags[DB_TITLE] is not None:
			trackStr += tags[DB_TITLE]
		self.trackText.setText(trackStr)
		
		if tags[DB_GENRE] is None:
			self.genreText.setText('')
		else:
			self.genreText.setText(tags[DB_GENRE])
	
	def DecreaseVolume(self):
		self.playerManager.player.DecreaseVolume()
		self.volumeBar.SetPercent(self.playerManager.player.GetVolume())
		#print(self.playerManager.player.GetVolume())   # TODO remove
	
	def IncreaseVolume(self):
		self.playerManager.player.IncreaseVolume()
		self.volumeBar.SetPercent(self.playerManager.player.GetVolume())
		#print(self.playerManager.player.GetVolume())   # TODO remove


class VolumeBar:
	"""Custom volume bar, designed only for use in this interface."""
	
	def __init__(self, parent, playerManager):
		self.parent = parent
		self.playerManager = playerManager
		
		self.volumeBarFill = QLabel(self.parent)
		self.volumeBarFill.setPixmap(QPixmap(os.path.join(imgDir, 'volume_bar_fill.png')))
		self.volumeBarFill.setStyleSheet('background: transparent;')   # Note: Only relevant if the image itself has transparency.
		self.volumeBarFill.move(0, VOLUME_BAR_TOP)   # We'll set the x position later.
		
		self.volumeBarShape = QLabel(self.parent)
		self.volumeBarShape.setPixmap(QPixmap(os.path.join(imgDir, 'volume_bar_opaque.png')))
		self.volumeBarShape.setStyleSheet('background: transparent;')
		#self.volumeBarShape.hide()   # TODO remove
		
		# Note: Since mouse tracking isn't enabled for this widget, the mouse move event will trigger only when a mouse button is pressed.
		self.volumeBarShape.mousePressEvent = self.mousePressVolumeBarShapeEvent
		self.volumeBarShape.mouseMoveEvent = self.mouseMoveVolumeBarShapeEvent
	
	def mousePressVolumeBarShapeEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			y = event.pos().y()
			self.volumeBarFill.resize(self.volumeBarFill.width(), VOLUME_BAR_HEIGHT - y)
			self.volumeBarFill.move(self.volumeBarFill.x(), VOLUME_BAR_TOP + y)
			QLabel.mousePressEvent(self.volumeBarShape, event)
			
			volumePercent = (VOLUME_BAR_HEIGHT - 1.0 - y) / (VOLUME_BAR_HEIGHT - 1)
			self.playerManager.SetVolume(volumePercent)
	
	def mouseMoveVolumeBarShapeEvent(self, event):
		# Nicely enough, Qt does most of the work here for us; it'll keep on sending the "drag" event even after the mouse moves away, as long as the button is still down.
		if event.buttons() & Qt.LeftButton:
			y = event.pos().y()
			if y < 0:
				y = 0
			if y >= VOLUME_BAR_HEIGHT:
				y = VOLUME_BAR_HEIGHT - 1
			self.volumeBarFill.resize(self.volumeBarFill.width(), VOLUME_BAR_HEIGHT - y)
			self.volumeBarFill.move(self.volumeBarFill.x(), VOLUME_BAR_TOP + y)
			QLabel.mouseMoveEvent(self.volumeBarShape, event)
			
			volumePercent = (VOLUME_BAR_HEIGHT - 1.0 - y) / (VOLUME_BAR_HEIGHT - 1)
			self.playerManager.SetVolume(volumePercent)
	
	def SetPercent(self, volumePercent):
		if volumePercent > 1:
			volumePercent = 1
		elif volumePercent < 0:
			volumePercent = 0
		
		y = int((VOLUME_BAR_HEIGHT - 1) * (1 - volumePercent))
		
		self.volumeBarFill.resize(self.volumeBarFill.width(), VOLUME_BAR_HEIGHT - y)
		self.volumeBarFill.move(self.volumeBarFill.x(), VOLUME_BAR_TOP + y)
		
		self.playerManager.SetVolume(volumePercent)


RunStdInterface(parentClass, MainWidget, config)


# NOTE: We would use this if using StdMainWindowBase.
#RunStdInterface(parentClass, MainWidget, config, bWindowUsesConfigFile=False)