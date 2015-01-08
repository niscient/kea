# Simple query table
#
# Notes:
#  


from qt import *
from kea_util import GetTableDB


class SimpleQueryTable(QTableView):
	"""A basic table which loads the result of a query. Doesn't include column headers."""
	
	def __init__(self, parent, x=None, y=None, width=None, height=None, query=None, dataColumn=0, columnSizes=None, db=None, bgColor='#ffffff', borderStyle=None, fontName='Arial', fontSize=8, fontColor='#000000', highlightColor='#cfc7d6', bAlternatingRowColors=False, scrollbarStyle=None, bUseSingleClickedAsDouble=False):
		"""Set up the table."""
		super(SimpleQueryTable, self).__init__(parent)
		self.parent = parent
		
		if width is not None and height is not None:
			self.resize(width, height)
		if x is not None and y is not None:
			self.move(x, y)
		
		if db is None:
			self.db = GetTableDB()
		else:
			self.db = db
		
		self.model = QSqlQueryModel()
		self.setModel(self.model)
		
		self.query = query
		self.dataColumn = dataColumn
		self.columnSizes = columnSizes
		if self.query is not None:
			self.LoadQuery(self.query, bLoadEvenIfSameQuery=True)
		
		self.fontName = fontName
		self.fontSize = fontSize
		self.setFont(QFont(self.fontName, self.fontSize))
		
		self.horizontalHeader().setStretchLastSection(True)
		self.horizontalHeader().hide()
		self.verticalHeader().hide()
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.setItemDelegate(self.NoFocusDelegate())
		self.setShowGrid(False)
		
		self.setAlternatingRowColors(bAlternatingRowColors)
		# This background color for a selected row would be used anyway when the table view has focus, but let's override things so it's used regardless of focus.
		palette = self.palette()
		palette.setColor(QPalette.Base, QColor(bgColor))
		#palette.setColor(QPalette.Base, QColor('#000000'))
		#palette.setColor(QPalette.Base, Qt.transparent)
		palette.setColor(QPalette.Text, QColor(fontColor))
		palette.setColor(QPalette.Highlight, QColor(highlightColor))
		palette.setColor(QPalette.HighlightedText, QColor(fontColor))
		self.setPalette(palette)
		
		if borderStyle is None:
			self.setStyleSheet('QTableView { border: 0px; }')
		else:
			self.setStyleSheet('QTableView { border: {}; }'.format(borderStyle))
		
		if scrollbarStyle is None:
			scrollbarStyle = '''
			QScrollBar:vertical { width: 14px; background-color: black; color: white; }
			QScrollBar:horizontal { height: 14px; background-color: black; color: white; }
			QScrollBar:sub-page, QScrollBar:add-page { background-color: black; }
			'''
		self.verticalScrollBar().setStyleSheet(scrollbarStyle)
		self.horizontalScrollBar().setStyleSheet(scrollbarStyle)
		
		self.onChooseCallback = None
		
		self.doubleClicked.connect(self.CellDoubleClicked)
		if bUseSingleClickedAsDouble:
			self.clicked.connect(self.CellDoubleClicked)
		
		self.installEventFilter(self)
		
		QShortcut(QKeySequence('Return'), self, self.OnEnter, context=Qt.WidgetShortcut)
		#QShortcut(QKeySequence('Delete'), self, self.OnDelete, context=Qt.WidgetShortcut)
	
	def eventFilter(self, obj, event):
		if event.type() == QEvent.KeyPress:
			key = event.key()
			modifiers = event.modifiers()
			if modifiers & Qt.ShiftModifier:
				key += Qt.SHIFT
			if modifiers & Qt.ControlModifier:
				key += Qt.CTRL
			if modifiers & Qt.AltModifier:
				key += Qt.ALT
			if modifiers & Qt.MetaModifier:
				key += Qt.META
			keySequence = QKeySequence(key)
			
			# Override default Home and End shortcuts.
			if keySequence == QKeySequence(QKeySequence.MoveToStartOfLine):
				self.scrollToTop()
				if self.model.rowCount() > 0:
					self.setCurrentIndex(self.model.index(0, 0))
				return True
			if keySequence == QKeySequence(QKeySequence.MoveToEndOfLine):
				self.scrollToBottom()
				if self.model.rowCount() > 0:
					self.setCurrentIndex(self.model.index(self.model.rowCount() - 1, 0))
				return True
			if keySequence == QKeySequence(QKeySequence.MoveToStartOfDocument):
				self.horizontalScrollBar().setSliderPosition(self.verticalScrollBar().minimum())
				return True
			if keySequence == QKeySequence(QKeySequence.MoveToEndOfDocument):
				self.horizontalScrollBar().setSliderPosition(self.verticalScrollBar().maximum())
				return True
			
			return False
			#return super(SimpleQueryTable, self).eventFilter(obj, event)   # TODO: Remove?
		return super(SimpleQueryTable, self).eventFilter(obj, event)
	
	def LoadQuery(self, query=None, bLoadEvenIfSameQuery=False, dataColumn=None, columnSizes=None):
		"""Load a new, possibly totally different query. Be careful with this function."""
		self._LoadQuery(query, bLoadEvenIfSameQuery=True)
		
		if dataColumn is not None:
			self.dataColumn = dataColumn
		if columnSizes is not None:
			self.columnSizes = columnSizes
		
		if self.columnSizes is not None:
			for i in range(len(self.columnSizes)):
				self.setColumnWidth(i, self.columnSizes[i])
	
	def _LoadQuery(self, query=None, bLoadEvenIfSameQuery=False):
		"""An internal function. Loads the table based on the query, but doesn't modify the various variables that keep track of how the data is sorted, etc. Uses the existing query if None is supplied."""
		if not bLoadEvenIfSameQuery and not BLibraryChanged() and (query is None or query == self.query):
			return False   # Prevent the current track from being reset if it's the exact same query, gotten say by clicking on the same directory again in the tree.
		if query is None:
			query = self.query
		
		# TODO remove?
		#AcceptCurrentLibrary()
		
		self.model.setQuery(query, self.db)
		while self.model.canFetchMore():
			self.model.fetchMore()
		self.query = query
		#print(self.query, '\n', sep='')
		return True
	
	def ReloadQuery(self):
		"""Reload the current query."""
		self._LoadQuery(self.query, bLoadEvenIfSameQuery=True)
	
	def ModifyQuery(self, queryModifyFunc, *queryModifyFuncArgs):
		"""Load a new query. The only argument that should be given is a modified version of the table's existing query, with a different set of path requirements."""
		# TODO if function behavior changes and we end up being allowed to call ModifyQuery() on queries that have different ORDER BY or column results, we'll need to change this function to set the values of sortedHeader, etc.
		self._LoadQuery(queryModifyFunc(self.query, *queryModifyFuncArgs))
	
	def CellDoubleClicked(self, index):
		row = index.row()
		data = self.model.data(self.model.index(row, self.dataColumn))
		if self.onChooseCallback is not None:
			self.onChooseCallback(data, row)
	
	def GetRowCount(self):
		return self.model.rowCount()
	
	def SelectRow(self, row):
		"""Selects a row. Doesn't clear current selection."""
		nextIndex = self.model.index(row, 0)
		# TODO delete one of these commands, they seem to do the same thing.
		self.setCurrentIndex(nextIndex)
		#self.selectionModel().select(nextIndex, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
	
	def OnEnter(self):
		if self.selectionModel().hasSelection():
			row = self.selectionModel().currentIndex().row()
			data = self.model.data(self.model.index(row, self.dataColumn))
			if self.onChooseCallback is not None:
				self.onChooseCallback(data, row)

	def ShowAndPreserveRow(self):
		"""Tables in Qt have a strange habit of advancing their rows when them go from invisible to visible. Calling this preserves the current row (though not multiple selections)."""
		#selectedRows = self.selectionModel().selectedRows()
		if self.selectionModel().hasSelection():
			row = self.selectionModel().currentIndex().row()
			# Upon hiding, Qt will already have moved to the next row, so we'll just cheat by moving back!
			row -= 1
			if row < 0:
				row = self.model.rowCount() - 1
			self.selectionModel().clearSelection()
			self.selectRow(row)
		self.show()
	
	class NoFocusDelegate(QItemDelegate):
		def drawFocus (self, painter, option, rect):
			option.state &= ~QStyle.State_HasFocus
			QItemDelegate.drawFocus(self, painter, option, rect)
	
	def SetItemCallback(self, func):
		"""Set a callback function to be run when an item is chosen. It must take a two arguments, a data value (from the data column specified in this class), and the row number."""
		self.onChooseCallback = func