# Standard media player (currently a Phonon wrapper)
#
# Notes:
#  

from __future__ import print_function
import os
from qt import *
from constants import DB_PATH
from util import PathNotExistError
import gbl
from kea_util import GetHoverButton, GetHoverButtonData, GetHoverButtonIconData
from tags import GetFileTags


class StdPlayer:
	"""Standard media player (currently a Phonon wrapper)."""
	
	def __init__(self):
		self.player = Phonon.MediaObject()
		self.audioOutput = Phonon.AudioOutput()
		Phonon.createPath(self.player, self.audioOutput)
		
		self._volumePercent = 1
		
		#self.SetTickCallback(self.Tick)   # TODO remove
	
	def SetSource(self, path):
		self.player.setCurrentSource(Phonon.MediaSource(path))
	
	def SetVolume(self, volumePercent):
		if volumePercent > 1:
			volumePercent = 1
		elif volumePercent < 0:
			volumePercent = 0
		
		self.audioOutput.setVolume(volumePercent)
		self._volumePercent = volumePercent
		#print('VOL_SET', self._volumePercent)   # TODO remove
	
	def GetVolume(self):
		return self._volumePercent
	
	def IncreaseVolume(self, incrPercent=.05):
		self._volumePercent += incrPercent
		if self._volumePercent > 1:
			self._volumePercent = 1
		self.audioOutput.setVolume(self._volumePercent)
		#print('VOL_INCR', self._volumePercent)   # TODO remove
	
	def DecreaseVolume(self, decrPercent=.05):
		self._volumePercent -= decrPercent
		if self._volumePercent < 0:
			self._volumePercent = 0
		elif self._volumePercent < 0.001:   # Deal with a potential problem with Python's rounding.
			self._volumePercent = 0
		self.audioOutput.setVolume(self._volumePercent)
		#print('VOL_DECR', self._volumePercent)   # TODO remove
	
	def BPlaying(self):
		return self.player.state() == Phonon.PlayingState
	
	def Play(self):
		self.player.play()
	
	def Pause(self):
		self.player.pause()
	
	def SetStateChangedCallback(self, func):
		"""Set a callback function to be run whenever the player state (paused, unpaused) changes."""
		self.player.stateChanged.connect(func)
	
	def SetTickCallback(self, func, tickInterval=1000):
		"""Set a callback function to be called every tickInterval milliseconds (default: 1000) the player plays for. The callback function must take an integer argument representing the player's current position in the track, in milliseconds."""
		self.player.setTickInterval(tickInterval)
		self.player.tick.connect(func)