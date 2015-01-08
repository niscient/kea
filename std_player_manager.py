# Standard player manager
#
# Notes:
#  


import os, random
from util import SQ
from qt import *
from constants import DB_PATH
from util import PathNotExistError
import gbl
from kea_util import ShowWarning, GetHoverButton, GetHoverButtonData, GetHoverButtonIconData
from tags import GetFileTags

from std_player import StdPlayer


class StdPlayerManager(QObject):
	"""Standard button manager. Takes care of track playback. Designed to interface with a track table."""
	
	def __init__(self, parent, trackTable=None, useObject=None):
		"""Set up the player manager. You can use 'trackTable' to set a usable track table, or you can do that later. You can set 'useObject' to set the object used to hold the GUI elements, if that object isn't the parent element of the player manager (which is assumed by default)."""
		super(StdPlayerManager, self).__init__(parent)
		self.parent = parent
		self.useObject = parent if useObject is None else useObject
		
		##--- Player
		
		self.player = StdPlayer()
		self.player.SetStateChangedCallback(self.PlayerStateChanged)
		
		self.bUserTriggeredState = False   # Keep track of which player states are manual. This will always be set before such a state is activated.
		
		
		##--- Buttons
		
		self.prevButton = None
		
		self.pauseButton = None
		self.playButtonIcon = self.playButtonHoverIcon = None
		self.pauseButtonIcon = self.pauseButtonHoverIcon = None
		self.bPaused = True   # Default starting state
		self.bPauseButtonHovered = False   # Default starting state
		
		self.nextButton = None
		
		self.playFileCallback = None
		
		self.trackTable = trackTable
	
	
	def eventFilter(self, obj, event):
		if obj == self.pauseButton:
			if event.type() == QEvent.Enter:
				if self.bPaused:
					self.pauseButton.setIcon(self.playButtonHoverIcon)
				else:
					self.pauseButton.setIcon(self.pauseButtonHoverIcon)
				self.bPauseButtonHovered = True
			elif event.type() == QEvent.Leave:
				if self.bPaused:
					self.pauseButton.setIcon(self.playButtonIcon)
				else:
					self.pauseButton.setIcon(self.pauseButtonIcon)
				self.bPauseButtonHovered = False
			return False
			#return super(StdPlayerManager, self).eventFilter(obj, event)   # TODO: Remove?
		else:
			return super(StdPlayerManager, self).eventFilter(obj, event)
	
	def AddPrevButton(self, imgPath, hoverImgPath, x, y):
		self.prevButton = GetHoverButton(self.useObject, imgPath, hoverImgPath)
		self.prevButton.move(x, y)
		self.prevButton.clicked.connect(self.PrevButton)
	
	def AddPauseButton(self, playImgPath, playHoverImgPath, pauseImgPath, pauseHoverImgPath, x, y):
		# The pause button images are too complicated to make work using just stylesheets, so we'll have to do things the hard way.
		self.pauseButton, self.playButtonIcon, self.playButtonHoverIcon = GetHoverButtonData(self.useObject, playImgPath, playHoverImgPath)
		self.pauseButtonIcon, self.pauseButtonHoverIcon = GetHoverButtonIconData(pauseImgPath, pauseHoverImgPath)
		self.pauseButton.move(x, y)
		
		self.bPaused = True   # Default starting state
		self.bPauseButtonHovered = False   # Default starting state
		
		self.pauseButton.clicked.connect(self.TogglePausedButton)
		self.pauseButton.installEventFilter(self)
	
	def AddNextButton(self, imgPath, hoverImgPath, x, y):
		self.nextButton = GetHoverButton(self.useObject, imgPath, hoverImgPath)
		self.nextButton.move(x, y)
		self.nextButton.clicked.connect(self.NextButton)
	
	def AddRandomButton(self, imgPath, hoverImgPath, x, y):
		self.randomButton = GetHoverButton(self.useObject, imgPath, hoverImgPath)
		self.randomButton.move(x, y)
		self.randomButton.clicked.connect(self.RandomButton)
	
	def PlayerStateChanged(self, new, old):
		if not self.bUserTriggeredState:
			if new != Phonon.PlayingState:   # A track has stopped playing.
				self.AutoNext()
		self.bUserTriggeredState = False
	
	def PrevButton(self):
		if self.trackTable is not None:
			self.trackTable.setFocus()
			self.Prev()
	
	def TogglePausedButton(self):
		# TODO possibly try to prevent focus from changing in the first place for this button.
		if self.trackTable is not None:
			self.trackTable.setFocus()
			self.TogglePaused()
	
	def NextButton(self):
		if self.trackTable is not None:
			self.trackTable.setFocus()
			self.Next()
	
	def RandomButton(self):
		if self.trackTable is not None:
			self.trackTable.setFocus()
			self.PlayRandom()
	
	def PlayFile(self, path):
		# It's a bother to grab all the tag data from the table (plus, maybe not all the columns are there), so we'll get it fresh at very little cost.
		
		oldDir = os.path.dirname(gbl.currentTrackPath) if gbl.currentTrackPath is not None else None
		gbl.currentTrackPath = path
		try:
			gbl.currentTrackTags = GetFileTags(path)
		except PathNotExistError as e:
			ShowWarning('No such file:', SQ(path))
			return
		
		tags = gbl.currentTrackTags
		
		self.bUserTriggeredState = True
		self.player.SetSource(tags[DB_PATH])
		self.SetPaused(False)
		
		if self.playFileCallback is not None:
			self.playFileCallback(tags)
	
	def _SetPausedState(self, bPaused):
		"""Set the player's paused state, including both the 'paused?' variable and the button image. Does not affect music playback directly."""
		self.bPaused = bPaused
		if self.bPaused:
			if self.bPauseButtonHovered:
				self.pauseButton.setIcon(self.playButtonHoverIcon)
			else:
				self.pauseButton.setIcon(self.playButtonIcon)
		else:
			if self.bPauseButtonHovered:
				self.pauseButton.setIcon(self.pauseButtonHoverIcon)
			else:
				self.pauseButton.setIcon(self.pauseButtonIcon)
	
	def SetPaused(self, bPaused):
		self._SetPausedState(bPaused)
		
		self.bUserTriggeredState = True
		if self.player.BPlaying():
			self.player.Pause()
		else:
			self.player.Play()
	
	def TogglePaused(self, onOff=None):
		"""Pause or unpause the player. Pass True for paused, False for not paused, or None to toggle the existing value."""
		bPaused = not self.bPaused if onOff is None else onOff
		self.SetPaused(bPaused)
	
	def Prev(self):
		if self.trackTable is not None:
			self.bUserTriggeredState = True
			if gbl.currentTrackRow is None:
				rowCount = self.trackTable.GetRowCount()
				if rowCount == 0:
					return
				gbl.currentTrackRow = 0   # TODO possibly set to last track instead; it's totally arbitrary.
			path, row = self.trackTable.GetPrevFileData(gbl.currentTrackRow)
			self.trackTable.clearSelection()
			self.trackTable.SelectRow(row)
			gbl.currentTrackRow = row
			self.PlayFile(path)
	
	def Next(self):
		if self.trackTable is not None:
			self.bUserTriggeredState = True
			if gbl.currentTrackRow is None:
				rowCount = self.trackTable.GetRowCount()
				if rowCount == 0:
					return
				gbl.currentTrackRow = rowCount - 1   # Set to the last track, so we start at the first.
			path, row = self.trackTable.GetNextFileData(gbl.currentTrackRow)
			self.trackTable.clearSelection()
			self.trackTable.SelectRow(row)
			gbl.currentTrackRow = row
			self.PlayFile(path)
	
	def AutoNext(self):
		"""Play the next track. Assumes that a track is already playing."""
		if self.trackTable is not None:
			if gbl.currentTrackRow is None:
				rowCount = self.trackTable.GetRowCount()
				if rowCount == 0:
					self.Replay()   # No valid table data? Just replay.
				gbl.currentTrackRow = rowCount - 1
			path, row = self.trackTable.GetNextFileData(gbl.currentTrackRow)
			self.trackTable.clearSelection()
			self.trackTable.SelectRow(row)
			gbl.currentTrackRow = row
			self.PlayFile(path)
	
	def PlayRandom(self):
		if self.trackTable is not None:
			self.bUserTriggeredState = True
			rowCount = self.trackTable.GetRowCount()
			if gbl.currentTrackRow is None:
				if rowCount == 0:
					return
			row = random.randint(0, rowCount - 1)
			path = self.trackTable.GetRowFileData(row)
			self.trackTable.clearSelection()
			self.trackTable.SelectRow(row)
			gbl.currentTrackRow = row
			self.PlayFile(path)
	
	def Replay(self):
		if gbl.currentTrackPath is not None:
			self.bUserTriggeredState = True
			if not os.path.isfile(gbl.currentTrackPath):
				ShowWarning('No such file:', SQ(gbl.currentTrackPath))
			else:
				self.player.SetSource(gbl.currentTrackPath)
				self.SetPaused(False)
	
	def SetVolume(self, volumePercent):
		self.player.SetVolume(volumePercent)
	
	def SetTrackTable(self, trackTable):
		self.trackTable = trackTable
	
	def SetPlayFileCallback(self, func):
		"""Set a callback function to be run when a file is loaded via this player. It must take a file tag structure (returned by GetFileTags()) as an argument."""
		self.playFileCallback = func