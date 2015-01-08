# Standard main menu functionality
#
# Notes:
#   The main menu class must be stored as an attribute (in other words, it must be stored
#  permanently) if it's used for a QMenuBar or if its shortcuts are expected to work even when
#  it's closed.


#!/usr/bin/env python

import sys, os, webbrowser

from qt import *
from util import RequiredImportError, SQ
from constants import *
import gbl
from kea_util import ShowMessage, ShowRestartChangesMessage
from db import GetLibraryDirs, BIsLibraryDir, BLibraryDirCovered, ResetDatabaseTags, ResetLibraryDirs
from walker import AddLibraryDirToDatabase, RemoveLibraryDirOrSubdirFromDatabase, RescanLibraryDirOrSubdir, RunLibraryChangedCallback
from config import GetInterfaceList, SetDefaultInterfaceName, ResetConfigFile


class StdMainMenu:
	"""Main menu class. Must be stored as an attribute (in other words, it must be stored permanently) if it's used for a QMenuBar or if its shortcuts are expected to work even when it's closed."""
	
	def __init__(self, parent, mainMenu):
		"""Adds the standard menus to a passed-in QMenuBar or QMenu."""
		
		self.parent = parent
		self.menu = mainMenu
		
		# File menu
		
		self.fileMenu = mainMenu.addMenu('&File')
		exitAction = QAction('&Exit', parent)
		exitAction.setShortcut('Ctrl+Q')
		if isinstance(mainMenu, QMenu):
			QShortcut(QKeySequence('Ctrl+Q'), parent, parent.close)
		exitAction.triggered.connect(parent.close)
		self.fileMenu.addAction(exitAction)
		
		# Edit menu
		
		#editMenu = mainMenu.addMenu('&Edit')
		
		# Library menu
		
		self.libraryMenu = mainMenu.addMenu('&Library')
		manageAction = QAction('&Manage', parent)
		manageAction.triggered.connect(self.ShowLibraryDialog)
		self.libraryMenu.addAction(manageAction)
		
		# Settings menu
		
		self.settingsMenu = mainMenu.addMenu('&Settings')
		
		interfaceSubMenu = self.settingsMenu.addMenu('&Interfaces')
		signalMapper = QSignalMapper(parent)
		signalMapper.mapped['QString'].connect(self.SetInterface)
		for interfaceName in GetInterfaceList():
			tempAction = QAction(interfaceName, parent)
			signalMapper.setMapping(tempAction, interfaceName)
			tempAction.triggered.connect(signalMapper.map)
			interfaceSubMenu.addAction(tempAction)
		
		resetInterfaceAction = QAction('&Reset Interface', parent)
		resetInterfaceAction.triggered.connect(self.ResetInterface)
		self.settingsMenu.addAction(resetInterfaceAction)
		
		# Help menu
		
		self.helpMenu = mainMenu.addMenu('&Help')
		websiteAction = QAction('&Website', parent)
		websiteAction.triggered.connect(self.ShowWebsite)
		aboutAction = QAction('&About', parent)
		aboutAction.triggered.connect(self.ShowAboutDialog)
		self.helpMenu.addActions([websiteAction, aboutAction])
	
	def ShowLibraryDialog(self):
		self.tempDialog = LibraryDialog(self.parent)   # Store this as an attribute to prevent it from being targeted by garbage collection.
	
	def SetInterface(self, identifier):
		SetDefaultInterfaceName(identifier)
		ShowRestartChangesMessage()
	
	def ResetInterface(self):
		reply = QMessageBox.question(self, 'Reset Interface', 'Reset interface to default configuration?', QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			ResetConfigFile()
			gbl.saveInterfaceChanges = False
			ShowRestartChangesMessage()
	
	def ShowWebsite(self):
		webbrowser.open(gbl.websiteAddress, autoraise=True)
	
	def ShowAboutDialog(self):
		self.tempDialog = AboutDialog(self.parent)


class LibraryDialog(QDialog):
	def __init__(self, parent=None):
		super(LibraryDialog, self).__init__(parent)
		self.parent = parent
		
		w, h = 400, 300   # Totally arbitrary, and not finally accurate.
		self.setFixedSize(w, h)
		# TODO maybe factor the window title height into the equation.
		self.move(parent.x() + parent.width()/2 - w/2, parent.y() + parent.height()/2 - h/2)
		self.setWindowTitle('Library')
		self.setModal(True)   # Easy way to prevent multiple instances.
		
		self.tempAddDir = None   # Used when adding directories.
		
		bigBox = QHBoxLayout()
		
		centerBox = QVBoxLayout()
		bigBox.addLayout(centerBox)
		
		self.list = QListWidget()
		centerBox.addWidget(self.list)
		
		lowerBox = QHBoxLayout()
		centerBox.addLayout(lowerBox)
		lowerBox.addSpacerItem(QSpacerItem(20, 1))
		rescanBtn = QPushButton('Re&scan')
		lowerBox.addWidget(rescanBtn)
		findNewFilesBtn = QPushButton('&Find New Files')
		lowerBox.addWidget(findNewFilesBtn)
		lowerBox.addSpacerItem(QSpacerItem(20, 1))
		
		sideBox = QVBoxLayout()
		bigBox.addLayout(sideBox)
		sideBox.addSpacerItem(QSpacerItem(1, 40))
		addBtn = QPushButton('&Add')
		sideBox.addWidget(addBtn)
		removeBtn = QPushButton('&Remove')
		sideBox.addWidget(removeBtn)
		clearBtn = QPushButton('C&lear')
		sideBox.addWidget(clearBtn)
		sideBox.addSpacerItem(QSpacerItem(1, 20))
		closeBtn = QPushButton('&Close')
		sideBox.addWidget(closeBtn)
		sideBox.addSpacerItem(QSpacerItem(1, 80))
		
		self.setLayout(bigBox)
		
		# TODO remove probably
		#style = "QDialog { background-color: white; } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#self.setStyleSheet(style)
		
		self.show()
		
		self.RefreshList()   # Must happen after calling show(), or the first item will auto-select for some reason, and show no highlighting.
		
		addBtn.clicked.connect(self.Add)
		removeBtn.clicked.connect(self.Remove)
		clearBtn.clicked.connect(self.Clear)
		closeBtn.clicked.connect(self.close)
		rescanBtn.clicked.connect(self.Rescan)
		findNewFilesBtn.clicked.connect(self.FindNewFiles)
	
	def RefreshList(self):
		self.list.clear()
		for dir in GetLibraryDirs():
			self.list.addItem(QListWidgetItem(dir))
	
	def Add(self):
		startDir = self.list.currentItem().text() if self.list.currentItem() is not None else QDir.currentPath()
		dir = QFileDialog.getExistingDirectory(self, 'Open Directory', startDir, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
		if len(dir) > 0:
			self.tempDialog = LoadingDialog(self.parent)
			self.tempAddDir = dir
			# In order to give the loading dialog "time" to become visually displayable, we'll perform the actual dir-adding procedure in a timer.
			QTimer.singleShot(1, self.DelayedAdd)
	
	def DelayedAdd(self):
		AddLibraryDirToDatabase(self.tempAddDir)
		self.RefreshList()
		self.tempDialog.close()
		self.tempAddDir = None
		
		if self.list.currentItem() is None:
			self.list.setCurrentRow(self.list.count() - 1)
	
	def Remove(self):
		if self.list.currentItem() is not None:
			reply = QMessageBox.question(self, 'Remove', 'Remove ' + SQ(self.list.currentItem().text()) + '?', QMessageBox.Yes | QMessageBox.No)
			if reply == QMessageBox.Yes:
				dir = self.list.currentItem().text()
				RemoveLibraryDirOrSubdirFromDatabase(dir, bCheckDir=False)
				self.RefreshList()
	
	def Clear(self):
		reply = QMessageBox.question(self, 'Clear', 'Remove all directories?', QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			ResetDatabaseTags()
			ResetLibraryDirs()
			self.RefreshList()
			RunLibraryChangedCallback()
	
	''' # TODO remove: Doesn't ask us to select subdir.
	def Rescan(self):
		if self.list.currentItem() is not None:
			dir = self.list.currentItem().text()
			RescanLibraryDirOrSubdir(dir, True, bCheckDir=False)
	'''
	
	def Rescan(self):
		"""Rescan a music library directory or subdirectory."""
		startDir = self.list.currentItem().text() if self.list.currentItem() is not None else QDir.currentPath()
		dir = QFileDialog.getExistingDirectory(self, 'Open Library Dir or Subdir', startDir, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
		if len(dir) > 0:
			if not BLibraryDirCovered(dir):
				ShowMessage('Please choose an existing library directory or subdirectory.')
			else:
				RescanLibraryDirOrSubdir(dir, True, bCheckDir=False)
	
	def FindNewFiles(self):
		"""Search for new files in a chosen music library dir or subdir"""
		startDir = self.list.currentItem().text() if self.list.currentItem() is not None else QDir.currentPath()
		dir = QFileDialog.getExistingDirectory(self, 'Open Library Dir or Subdir', startDir, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
		if len(dir) > 0:
			if not BLibraryDirCovered(dir):
				ShowMessage('Please choose an existing library directory or subdirectory.')
			else:
				RescanLibraryDirOrSubdir(dir, False, bCheckDir=False)


class AboutDialog(QDialog):
	def __init__(self, parent=None):
		super(AboutDialog, self).__init__(parent)
		
		w, h = 580, 270   # Totally arbitrary, and not finally accurate.
		self.setFixedSize(w, h)
		# TODO maybe factor the window title height into the equation.
		self.move(parent.x() + parent.width()/2 - w/2, parent.y() + parent.height()/2 - h/2)
		self.setWindowTitle('About')
		self.setModal(True)   # Easy way to prevent multiple instances.
		
		# TODO maybe set positions by coordinates instead of doing it this way.
		
		font = QFont('Arial', 9)
		hbox = QHBoxLayout()
		
		pixmapLbl = QLabel()
		pixmapLbl.setPixmap(QPixmap(os.path.join(gbl.imgDir, 'about.png')))
		hbox.addWidget(pixmapLbl)
		hbox.addSpacerItem(QSpacerItem(40, 1))
		
		vbox = QVBoxLayout()
		vbox.addSpacerItem(QSpacerItem(1, 30))
		titleLbl = QLabel()
		titleLbl.setPixmap(QPixmap(os.path.join(gbl.imgDir, 'about_title_dark_fade.png')))
		vbox.addWidget(titleLbl)
		vbox.addSpacerItem(QSpacerItem(1, 30))
		lbl1 = QLabel()
		lbl1.setText("<font color='black'>    1.0</font>")
		lbl1.setFont(font)
		vbox.addWidget(lbl1)
		lbl2 = QLabel()
		lbl2.setText("<font color='black'>  Rains Jordan</font>")
		lbl2.setFont(font)
		vbox.addWidget(lbl2)
		vbox.addSpacerItem(QSpacerItem(1, 30))
		okBtn = QPushButton('OK')
		vbox.addWidget(okBtn)
		vbox.addSpacerItem(QSpacerItem(1, 10))
		
		hbox.addLayout(vbox)
		hbox.addSpacerItem(QSpacerItem(50, 1))
		self.setLayout(hbox)
		
		# TODO remove old ones (most recent first)
		
		style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d0d0d0, stop: .2 #b8b8b8, stop: .21 #eaeaea, stop: .211 #d5d5d5, stop: .35 #c0c0c0, stop: .44 #b3b3b3, stop: .45 #dddddd, stop: .451 #9a9a9a, stop: .86 #b8b8b8, stop: .87 #d5d5d5, stop: .873 #aaaaaa, stop: 1 #8d8d8d); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d0d0d0, stop: .2 #b8b8b8, stop: .21 #d5d5d5, stop: .211 #d5d5d5, stop: .35 #c0c0c0, stop: .44 #b3b3b3, stop: .441 #a5a5a5, stop: .86 #b8b8b8, stop: .87 #d5d5d5, stop: .88 #aaaaaa, stop: 1 #8d8d8d); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d0d0d0, stop: .2 #b8b8b8, stop: .21 #d5d5d5, stop: .211 #d5d5d5, stop: .45 #d5d5d5, stop: .47 #c0c0c0, stop: .471 #a5a5a5, stop: .86 #b8b8b8, stop: .87 #d5d5d5, stop: .88 #aaaaaa, stop: 1 #8d8d8d); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		
		# the other good one
		#style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d0d0d0, stop: .2 #b8b8b8, stop: .21 #d5d5d5, stop: .211 #b8b8b8, stop: .45 #b7b7b7, stop: .47 #d5d5d5, stop: .471 #aeaeae, stop: .86 #b8b8b8, stop: .87 #d5d5d5, stop: .88 #aaaaaa, stop: 1 #8d8d8d); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		
		#style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d0d0d0, stop: .2 #b8b8b8, stop: .21 #d5d5d5, stop: .211 #b8b8b8, stop: .45 #b7b7b7, stop: .47 #d5d5d5, stop: .471 #aeaeae, stop: .81 #b8b8b8, stop: .82 #d5d5d5, stop: .821 #aaaaaa, stop: 1 #8d8d8d); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d0d0d0, stop: .45 #b7b7b7, stop: .47 #d5d5d5, stop: .471 #aeaeae, stop: 1 #8d8d8d); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#style = "QDialog { background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #b8b8b8, stop: .51 #b7b7b7, stop: .511 #aeaeae, stop: 1 #a0a0a0); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#style = "QDialog { background: QLinearGradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #000000, stop: .5 #ffffff, stop: .5 #ffffff, stop: 1 #000000); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		#style = "QDialog { background: QLinearGradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffffff, stop: 1 #000000); } QPushButton { border: 2px solid black; background-color: #f2f2f2; }"
		self.setStyleSheet(style)
		
		self.show()
		
		okBtn.clicked.connect(self.close)


class LoadingDialog(QDialog):
	def __init__(self, parent=None):
		super(LoadingDialog, self).__init__(parent)
		
		# TODO maybe try making this work. Maybe not.
		#w, h = 128, 31   # Image size.
		#self.setFixedSize(w, h)
		
		pixmap = QPixmap(os.path.join(gbl.imgDir, 'loading.png'))
		w = pixmap.width()
		h = pixmap.height()
		
		# TODO maybe factor the window title height into the equation.
		self.move(parent.x() + parent.width()/2 - w/2, parent.y() + parent.height()/2 - h/2)
		self.setWindowTitle('Loading')
		self.setModal(True)   # Easy way to prevent multiple instances.
		
		# TODO maybe set positions by coordinates instead of doing it this way.
		
		lbl = QLabel(self)
		'''lbl.setText('loading')
		lbl.setFont(QFont('Arial', 9))
		lbl.setStyleSheet('QLabel { color: white; }')'''
		lbl.setPixmap(pixmap)
		
		hbox = QHBoxLayout()
		hbox.addWidget(lbl)
		self.setLayout(hbox)
		
		#style = "QDialog { background-color: black; }"
		#self.setStyleSheet(style)
		
		self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
		lbl.setAlignment(Qt.AlignHCenter)
		lbl.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
		
		# TODO why do those gray borders appear anyway?
		#self.setAttribute(Qt.WA_NoSystemBackground)
		self.setAttribute(Qt.WA_TranslucentBackground)
		#self.setAttribute(Qt.WA_PaintOnScreen)
		
		self.show()