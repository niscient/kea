# Simple query track table
#
# Notes:
#  


from qt import *
from gbl import ResetCurrentTrackRow, BLibraryChanged, AcceptCurrentLibrary
from walker import RemoveFileFromDatabase
from simple_query_table import SimpleQueryTable


class SimpleTrackQueryTable(SimpleQueryTable):
	"""A basic table which loads track results from a query. Doesn't include column headers."""
	
	def __init__(self, parent, x=None, y=None, width=None, height=None, selectQueryPart=None, whereQueryPart=None, orderBy=None, columnSizes=None, db=None, bgColor='#ffffff', borderStyle=None, fontName='Arial', fontSize=8, fontColor='#000000', highlightColor='#cfc7d6', bAlternatingRowColors=False, scrollbarStyle=None, bUseSingleClickedAsDouble=False):
		super(SimpleTrackQueryTable, self).__init__(parent, x, y, width, height, None, None, columnSizes, db, bgColor, borderStyle, fontName, fontSize, fontColor, highlightColor, bAlternatingRowColors, scrollbarStyle, bUseSingleClickedAsDouble)
		
		# Set up various important details.
		self.dataColumn = None   # The path column. Important: This must be set manually later if no selectQueryPart is given.
		self.bHidePathColumn = True   # We always need a path column so the data will be accessible.
		
		if selectQueryPart is not None:
			self.CreateQuery(selectQueryPart, whereQueryPart, orderBy)
		
		self.libChangedCallbackArgs = None   # This allows us to tell the library changed callback function to not redraw certain things, if they don't need to be redrawn.
		
		QShortcut(QKeySequence('Delete'), self, self.OnDelete, context=Qt.WidgetShortcut)
	
	def CreateQuery(self, selectQueryPart, whereQueryPart=None, orderBy=None):
		self.query = 'SELECT '
		
		self.query += selectQueryPart
		
		selectParts = selectQueryPart.split(', ')
		self.dataColumn = selectParts.index('title') if 'path' in selectParts else None
		if self.dataColumn is None:   # The path needs to be in our results somewhere, so generate and hide it if necessary.
			if len(selectParts) > 0:
				self.query += ', path'
			else:
				self.query += 'path'
			self.dataColumn = len(selectParts)
		else:
			self.bHidePathColumn = False
		
		# TODO remove
		# The initial query behavior. Note that we create an extra column as padding.
		#self.query += " NULL AS '' FROM File, Artist, Album, Genre WHERE File.artistid == Artist.artistid AND File.albumid == Album.albumid AND File.genreid == Genre.genreid ORDER BY "
		
		self.query += ' FROM File, Artist, Album, Genre WHERE File.artistid == Artist.artistid AND File.albumid == Album.albumid AND File.genreid == Genre.genreid '
		
		if whereQueryPart is not None and len(whereQueryPart) > 0:
			self.query += 'AND ' + whereQueryPart
		
		if self.query[-1] != ' ':
			self.query += ' '
		
		if orderBy is not None and len(orderBy) > 0:
			self.query += 'ORDER BY ' + orderBy
		else:
			self.query += 'ORDER BY artist COLLATE NOCASE ASC, album COLLATE NOCASE ASC, track'
		
		# TODO remove
		#self.sortedHeader = 'artist'
		#self.sorted = SORTED_ASC
		
		self._LoadQuery(self.query, bLoadEvenIfSameQuery=True)
		
		#print(self.query)   # TODO remove
		
		if self.columnSizes is not None:
			for i in range(len(self.columnSizes)):
				self.setColumnWidth(i, self.columnSizes[i])
	
	
	def _LoadQuery(self, query=None, bLoadEvenIfSameQuery=False):
		"""An internal function. Loads the table based on the query, but doesn't modify the various variables that keep track of how the data is sorted, etc. Uses the existing query if None is supplied."""
		if not bLoadEvenIfSameQuery and not BLibraryChanged() and (query is None or query == self.query):
			return False   # Prevent the current track from being reset if it's the exact same query, gotten say by clicking on the same directory again in the tree.
		if query is None:
			query = self.query
		
		# TODO keep? remove? remove.
		#AcceptCurrentLibrary()
		ResetCurrentTrackRow()   # You should call this, or reset the associated global variable directly, whenever changing track table data.
		
		self.model.setQuery(query, self.db)
		while self.model.canFetchMore():
			self.model.fetchMore()
		if self.bHidePathColumn:
			self.setColumnHidden(self.dataColumn, True)
		self.query = query
		#print(self.query, '\n', sep='')
		return True
	
	def GetPrevFileData(self, row):
		"""Get a tuple: (path, row), for the previous file before the one in the given row."""
		prevRow = row - 1
		path = self.model.data(self.model.index(prevRow, self.dataColumn))
		if path is None:
			prevRow = self.model.rowCount() - 1
			path = self.model.data(self.model.index(prevRow, self.dataColumn))
			if path is None:
				raise LogicError("Invalid path. (Out-of-date current track row wasn't reset.)")
		return path, prevRow
	
	def GetNextFileData(self, row):
		"""Get a tuple: (path, row), for the next file after the one in the given row."""
		nextRow = row + 1
		path = self.model.data(self.model.index(nextRow, self.dataColumn))
		if path is None:
			nextRow = 0
			path = self.model.data(self.model.index(nextRow, self.dataColumn))
			if path is None:
				raise LogicError("Invalid path. (Out-of-date current track row wasn't reset.)")
		return path, nextRow
	
	def GetRowFileData(self, row):
		"""Get the path for a file on a specific row."""
		path = self.model.data(self.model.index(row, self.dataColumn))
		if path is None:
			raise LogicError("Invalid path. (Out-of-date current track row wasn't reset.)")
		return path
	
	def contextMenuEvent(self, event):
		menu = QMenu()
		deleteAction = menu.addAction('&Delete')
		deleteAction.triggered.connect(self.OnDelete)
		# TODO is there any way to make the popup() function work, instead of exec_()? doesn't really matter though, it's not like it stalls the program or anything.
		menu.exec_(QCursor.pos())
	
	def OnDelete(self):
		selectModel = self.selectionModel()
		if selectModel.hasSelection():
			rowIndexes = selectModel.selectedRows()
			deleteNum = len(rowIndexes)
			trackStr = 'track' if deleteNum == 1 else 'tracks'
			reply = QMessageBox.question(self, 'Delete', 'Delete ' + str(deleteNum) + ' ' + trackStr + '?', QMessageBox.Yes | QMessageBox.No)
			if reply == QMessageBox.Yes:
				# Note: It's crucial to get all the paths before we start deleting things, or we could be dealing with out-of-date rows.
				paths = [self.model.data(self.model.index(index.row(), self.dataColumn)) for index in rowIndexes]
				for path in paths:
					if self.libChangedCallbackArgs is not None:
						RemoveFileFromDatabase(path, libChangedCallbackArgs=self.libChangedCallbackArgs)
					else:
						RemoveFileFromDatabase(path)
				self._LoadQuery(self.query, bLoadEvenIfSameQuery=True)   # QtSqlQueryModel is read-only. We can't remove rows, so let's just reload the query.