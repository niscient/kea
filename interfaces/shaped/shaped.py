# shaped
# Created by Rains Jordan
# Last updated 12/4/14
#
# Non-standard shortcuts:
#   Alt+Left: Back
#   Alt+Right: Forward (Enter)
#
# Notes:
#   This is a simple demonstration of a sample kea interface, using a widget-like interface with
#  multiple simple tables. One table is used to list artists, one is used to list albums, and one
#  is used to list music tracks.
#
# Implementation notes:
#   This file is smaller and simpler than the Rectangular interface, since it primarily extends
#  standard kea library functionality.
#
# To do:
#  


#!/usr/bin/env python

from __future__ import absolute_import, print_function
if __name__ == '__main__':
	import direct_test_enabler   # Make the interface runnable directly, for testing purposes. This should be done before most of the other imports.

from std_interface_imports import *
from util import ShortenStr
from kea_util import InsertArtistSearchIntoQuery, InsertAlbumSearchIntoQuery

from shaped_main_window import ShapedMainWindow
from std_player_manager import StdPlayerManager
from std_progress_bar import StdProgressBar
from img_volume_bar import ImgVolumeBar
from simple_query_table import SimpleQueryTable
from simple_track_query_table import SimpleTrackQueryTable


config = GetConfigFile()
imgDir = GetImgDir()

MAX_TRACK_TEXT_LEN = 36   # 40 should be fine, too, space-wise.


class MainWidget(QWidget):
	def __init__(self, parent):   # The main widget should take the main window as its first argument.
		super(MainWidget, self).__init__(parent)
		self.parent = parent
		
		self.db = GetTableDB()
		
		scrollbarStyle = '''
		QScrollBar::handle { background-color: #323232; border: 1px solid #2d2d2d; min-height: 14px; min-width: 14px; }
		/*QScrollBar::handle { background-color: #8f8a5d; border: 1px solid #5e5c4f; min-height: 14px; min-width: 14px; }*/
		QScrollBar:horizontal { height: 6px; background: transparent; }
		QScrollBar:vertical { width: 6px; background: transparent; }
		QScrollBar:up-arrow { background: transparent; border: 0px; }
		QScrollBar:down-arrow { background: transparent; border: 0px; }
		QScrollBar:sub-page, QScrollBar:add-page { background: transparent; }
		QScrollBar::add-line { width: 0px; height: 0px; }
		QScrollBar::sub-line { width: 0px; height: 0px; }
		'''
		
		commonTableArgs = (self, 25, 52, 378, 150)
		commonTableKwArgs = {'db':self.db, 'bgColor':'#141313', 'fontName':'Georgia', 'fontColor':'#8f8a5d', 'highlightColor':'#2f3026', 'scrollbarStyle':scrollbarStyle, 'bUseSingleClickedAsDouble':True}
		
		self.trackTable = SimpleTrackQueryTable(*commonTableArgs, selectQueryPart='track, title', orderBy='track', columnSizes=(40,), **commonTableKwArgs)
		self.trackTable.SetItemCallback(self.ChooseTrack)
		self.trackTable.hide()
		
		self.artistTable = SimpleQueryTable(*commonTableArgs, query="SELECT artist from Artist WHERE artist <> '' ORDER BY artist COLLATE NOCASE ASC", **commonTableKwArgs)
		self.artistTable.SetItemCallback(self.ChooseArtist)
		self.artistTable.hide()
		
		self.albumTable = SimpleQueryTable(*commonTableArgs, **commonTableKwArgs)
		self.albumTable.SetItemCallback(self.ChooseAlbum)
		self.albumTable.hide()
		
		self.mainFrame = MainFrame(self)
		
		
		##--- Textual info
		
		trackFontName = config.get('General', 'trackFontName')
		trackFontSize = int(config.get('General', 'trackFontSize'))
		trackFontColor = config.get('General', 'trackFontColor')
		
		self.trackText = QLabel(self)
		self.trackText.setFont(QFont(trackFontName, trackFontSize))
		self.trackText.setAttribute(Qt.WA_TranslucentBackground)
		self.trackText.setTextFormat(Qt.RichText)   # Possibly unnecessary.
		self.trackText.setStyleSheet('QLabel { color: #7d811e; }')
		self.trackText.move(49, 22)
		self.trackText.mouseMoveEvent = self.mouseMoveEvent
		
		
		#--- Control bar
		
		controlShadows = QLabel(self)
		controlShadows.setPixmap(QPixmap(os.path.join(imgDir, 'control_shadows.png')))
		controlShadows.move(52, 206)
		
		self.playerManager = StdPlayerManager(self, trackTable=self.trackTable)
		self.playerManager.AddPrevButton(os.path.join(imgDir, 'prev_button.png'), os.path.join(imgDir, 'prev_button_hover.png'), 90, 219)
		self.playerManager.AddPauseButton(os.path.join(imgDir, 'play_button.png'), os.path.join(imgDir, 'play_button_hover.png'), os.path.join(imgDir, 'pause_button.png'), os.path.join(imgDir, 'pause_button_hover.png'), 143, 219)
		self.playerManager.AddNextButton(os.path.join(imgDir, 'next_button.png'), os.path.join(imgDir, 'next_button_hover.png'), 183, 219)
		self.playerManager.AddRandomButton(os.path.join(imgDir, 'random_button.png'), os.path.join(imgDir, 'random_button_hover.png'), 234, 219)
		self.playerManager.SetPlayFileCallback(self.PlayFileCallback)
		
		# TODO at some point
		#self.playerManager.AddRandomArtistButton(os.path.join(imgDir, 'random_artist_button.png'), os.path.join(imgDir, 'random_artist_button_hover.png'))
		
		
		##--- The rest of the widget
		
		self.bubbleMenu = QLabel(self)
		self.bubbleMenu.setPixmap(QPixmap(os.path.join(imgDir, 'bubble_menu.png')))
		self.bubbleMenu.move(340, 16)
		
		# Note: The volume bar should go after the control bar in case there are image overlaps.
		self.volumeBar = ImgVolumeBar(self, os.path.join(imgDir, 'volume_bar_bg.png'), os.path.join(imgDir, 'volume_bar_fill.png'), bVertical=False)
		self.volumeBar.move(52, 206)
		self.volumeBar.bg.move(0, 14)
		self.volumeBar.SetVolumeChangedCallback(self.VolumeChangedCallback)
		
		progressBarStyle = '''
		QSlider { height: 6px;  }
		QSlider::handle { width: 10px; background-color: #73771e; border: 1px solid #555916; }
		QSlider::groove { background-color: transparent; }
		'''
		self.progressBar = StdProgressBar(self, 100, -7, 118, 50, self.playerManager.player, progressBarStyle)
		
		self.backButton = GetHoverButton(self, os.path.join(imgDir, 'back_button.png'), os.path.join(imgDir, 'back_button_hover.png'))
		self.backButton.move(8, 115)
		self.backButton.clicked.connect(self.BackButton)
		self.backButton.hide()
		
		self.tableStack = []   # Keep track of the recent parent tables.
		
		SetLibraryChangedCallback(self.LibraryChangedCallback)
		
		CreateStdHotkeys(self, self.playerManager, config)
		
		# TODO: Not currently necessary, but I might bring this back at some point.
		#QShortcut(QKeySequence('Ctrl+R'), self, self.OnFocusTable)
		
		QShortcut(QKeySequence(Qt.ALT + Qt.Key_Left), self, self.BackButton)
		QShortcut(QKeySequence(Qt.ALT + Qt.Key_Right), self, self.FrontButton)
		
		QShortcut(QKeySequence('Ctrl+Alt+Up'), self, self.IncreaseVolume)
		QShortcut(QKeySequence('Ctrl+Alt+Down'), self, self.DecreaseVolume)
	
	def LibraryChangedCallback(self):
		self.trackTable.ReloadQuery()
		self.artistTable.ReloadQuery()
		self.albumTable.ReloadQuery()
		AcceptCurrentLibrary()
	
	'''
	def OnFocusTable(self):
		if len(self.tableStack) > 0:
			self.tableStack[-1].setFocus()
	'''
	
	def mousePressEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			if self.bubbleMenu.frameGeometry().contains(event.pos()):
				self.parent.ShowMainMenu(self.mapToGlobal(event.pos()))
		super(MainWidget, self).mousePressEvent(event)
	
	def PlayFileCallback(self, tags):
		artist = tags[DB_ARTIST]
		title = tags[DB_TITLE]
		self.trackText.setText(ShortenStr(artist + ': ' + title, MAX_TRACK_TEXT_LEN, 'r'))
		self.trackText.resize(self.width(), self.trackText.height())
	
	def VolumeChangedCallback(self, volumePercent):
		self.playerManager.SetVolume(volumePercent)
	
	def BackButton(self):
		if len(self.tableStack) > 0:
			currentTable = self.tableStack.pop()
			if len(self.tableStack) > 0:
				prevTable = self.tableStack[-1]
				prevTable.ShowAndPreserveRow()
				prevTable.setFocus()
			else:
				self.mainFrame.show()
				self.backButton.hide()
				self.mainFrame.setFocus()
			currentTable.hide()
	
	def FrontButton(self):
		QApplication.sendEvent(QApplication.focusWidget(), QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
	
	def ChooseTrack(self, path, row):
		gbl.currentTrackRow = row
		self.playerManager.PlayFile(path)
	
	def ChooseArtist(self, artist, row):
		artistAlbumQuery = "SELECT album FROM AlbumContainsArtist, Album, Artist WHERE AlbumContainsArtist.artistid=Artist.artistid AND AlbumContainsArtist.albumid=Album.albumid ORDER BY album COLLATE NOCASE ASC"
		self.albumTable.LoadQuery(InsertArtistSearchIntoQuery(artistAlbumQuery, artist))
		self.albumTable.show()
		self.artistTable.hide()
		self.tableStack.append(self.albumTable)
		self.albumTable.setFocus()
		self.albumTable.clearSelection()
		self.albumTable.selectRow(0)
		self.albumTable.scrollToTop()
	
	def ChooseAlbum(self, album, row):
		self.trackTable.ModifyQuery(InsertAlbumSearchIntoQuery, album)
		self.trackTable.show()
		self.albumTable.hide()
		self.tableStack.append(self.trackTable)
		self.trackTable.setFocus()
		if gbl.currentTrackRow is None:
			self.trackTable.clearSelection()
			self.trackTable.selectRow(0)
			self.trackTable.scrollToTop()
	
	def IncreaseVolume(self):
		self.playerManager.player.IncreaseVolume()
		self.volumeBar.SetPercent(self.playerManager.player.GetVolume())
	
	def DecreaseVolume(self):
		self.playerManager.player.DecreaseVolume()
		self.volumeBar.SetPercent(self.playerManager.player.GetVolume())


class MainFrame(QFrame):
	"""Main frame. Intricately connected with the main widget class."""
	
	def __init__(self, parent):
		super(MainFrame, self).__init__(parent)
		self.parent = parent
		
		#self.bg = QLabel(self)
		#self.bg.setPixmap(QPixmap(os.path.join(imgDir, )))
		#self.bg.setText('wut')
		
		self.selectionPixmap = QPixmap(os.path.join(imgDir, 'selection_bar.png'))
		
		self.artistsBG = QLabel(self)
		self.artistsBG.setPixmap(self.selectionPixmap)
		self.artistsBG.move(12, 42)
		self.artistsBG.resize(self.selectionPixmap.size())
		self.artistsBG.hide()
		
		self.albumsBG = QLabel(self)
		self.albumsBG.setPixmap(self.selectionPixmap)
		self.albumsBG.move(12, 89)
		self.albumsBG.resize(self.selectionPixmap.size())
		self.albumsBG.hide()
		
		self.artistsButton = GetHoverButton(self, os.path.join(imgDir, 'artists.png'), os.path.join(imgDir, 'artists_hover.png'), bFocusable=True)
		self.artistsButton.move(41, 75)
		self.artistsButton.enterEvent = self.enterArtistsButtonEvent
		self.artistsButton.leaveEvent = self.leaveArtistsButtonEvent
		self.artistsButton.focusInEvent = self.focusInArtistsButtonEvent
		self.artistsButton.clicked.connect(self.ArtistsButton)
		self.artistsButton.setAutoDefault(True)
		
		self.albumsButton = GetHoverButton(self, os.path.join(imgDir, 'albums.png'), os.path.join(imgDir, 'albums_hover.png'), bFocusable=True)
		self.albumsButton.move(41, 122)
		self.albumsButton.enterEvent = self.enterAlbumsButtonEvent
		self.albumsButton.leaveEvent = self.leaveAlbumsButtonEvent
		self.albumsButton.focusInEvent = self.focusInAlbumsButtonEvent
		self.albumsButton.clicked.connect(self.AlbumsButton)
		self.albumsButton.setAutoDefault(True)
		
		self.focused = None   # Keep track of which menu item has been manually selected, using keyboard navigation. (If using the mouse, this is not used.)
		
		QShortcut(QKeySequence('Escape'), self, self.RemoveFocus)
		
		self.artistsButton.setFocusPolicy(Qt.NoFocus)
		self.albumsButton.setFocusPolicy(Qt.NoFocus)
		QTimer.singleShot(200, self.SetFocusable)   # Override Qt's default behavior by not introducing immediate focus markers.
	
	def resizeEvent(self, event):
		self.resize(self.parent.size())
	
	def focusInEvent(self, event):
		if self.focused == self.artistsButton:
			self.artistsButton.setFocus()
		elif self.focused == self.albumsButton:
			self.albumsButton.setFocus()
		super(MainFrame, self).focusInEvent(event)
	
	def enterArtistsButtonEvent(self, event):
		self.artistsBG.show()
		self.albumsBG.hide()
	
	def enterAlbumsButtonEvent(self, event):
		self.artistsBG.hide()
		self.albumsBG.show()
	
	def leaveArtistsButtonEvent(self, event):
		self.artistsBG.hide()
	
	def leaveAlbumsButtonEvent(self, event):
		self.albumsBG.hide()
	
	def focusInArtistsButtonEvent(self, event):
		if event.reason() == Qt.TabFocusReason or event.reason() == Qt.BacktabFocusReason:
			self.focused = self.artistsButton
		QPushButton.focusInEvent(self.artistsButton, event)
	
	def focusInAlbumsButtonEvent(self, event):
		if event.reason() == Qt.TabFocusReason or event.reason() == Qt.BacktabFocusReason:
			self.focused = self.albumsButton
		QPushButton.focusInEvent(self.albumsButton, event)
	
	def ArtistsButton(self):
		self.parent.artistTable.show()
		self.parent.backButton.show()
		self.hide()
		self.parent.tableStack.append(self.parent.artistTable)
		self.parent.artistTable.setFocus()
		self.parent.artistTable.clearSelection()
		self.parent.artistTable.selectRow(0)
		self.parent.artistTable.scrollToTop()
	
	def AlbumsButton(self):
		# Clear any previous search criteria.
		self.parent.albumTable.LoadQuery("SELECT album from Album WHERE album <> '' ORDER BY album COLLATE NOCASE ASC")
		self.parent.trackTable.CreateQuery('track, title', '', orderBy='track')
		
		self.parent.albumTable.show()
		self.parent.backButton.show()
		self.hide()
		self.parent.tableStack.append(self.parent.albumTable)
		self.parent.albumTable.setFocus()
		self.parent.albumTable.clearSelection()
		self.parent.albumTable.selectRow(0)
		self.parent.albumTable.scrollToTop()
	
	def SetFocusable(self):
		self.artistsButton.setFocusPolicy(Qt.TabFocus)
		self.albumsButton.setFocusPolicy(Qt.TabFocus)
	
	def RemoveFocus(self):
		self.artistsButton.clearFocus()
		self.albumsButton.clearFocus()


RunShapedInterface(ShapedMainWindow, os.path.join(imgDir, 'player_shape.png'), MainWidget, config)