# Dir system model
#
# Notes:
#  An item model which can be used with a customized QTreeView to navigate the music library.
#
# Config file usage:
#   Program->bRemoveSingleTreeRootNode: Stores whether the tree node will display a solo root
#  node, or whether it'll only display its contents.


import os

try:
	import configparser
except ImportError:
	import ConfigParser as configparser

from qt import *
from db import GetLibraryDirs


# Notable default values for optional config file settings.
B_REMOVE_SINGLE_TREE_ROOT_NODE = False


def GetBRemoveSingleTreeRootNode(config):
	"""Is the 'Program->bRemoveSingleTreeRootNode' setting True?"""
	try:
		bRemoveSingleTreeRootNode = config.get('Program', 'bRemoveSingleTreeRootNode').lower() == 'true'
	except configparser.NoOptionError:
		bRemoveSingleTreeRootNode = B_REMOVE_SINGLE_TREE_ROOT_NODE
	return bRemoveSingleTreeRootNode

class DirSystemModel(QStandardItemModel):
	"""
	An item model that can be used with a customized QTreeView to navigate the music library.
	This is a 2-layer model which always retrieves two layers of data when a branch of it is expanded. This means that branch symbols will appear even for branches the user hasn't yet navigated.
	Quick guide:
	Call Reload() to reload the model from the music library.
	Call AllowExpandLayer() on the QTreeView's current index when a tree branch is expanded.
	Call dir() to get the dir at an index.
	"""
	
	def __init__(self, parent, configFile):   # A parent is basically optional, but PyQt complains if you don't give one.
		super(DirSystemModel, self).__init__(parent)
		self.bUseRootBaseName = None
		self.processedLayers = None
		self.configFile = configFile
		self.Reload()
	
	def Reload(self):
		"""Reload the contents of the model."""
		self.clear()
		self.bUseRootBaseName = None
		self.processedLayers = []
		libraryDirs = GetLibraryDirs()
		
		if GetBRemoveSingleTreeRootNode(self.configFile) and len(libraryDirs) < 2:
			# Don't add the roots themselves as nodes.
			for rootDir in libraryDirs:
				self.bUseRootBaseName = True
				if os.path.isdir(rootDir):
					for name in os.listdir(rootDir):
						if os.path.isdir(os.path.join(rootDir, name)):
							item = QStandardItem(name)
							setattr(item, 'rootDir', rootDir)
							self.appendRow(item)
							self.AddLayer(os.path.join(rootDir, name), item, bSettingUp=True)
		else:
			# Add the roots themselves as nodes.
			bFirst = True
			for rootDir in GetLibraryDirs():
				self.bUseRootBaseName = False
				if os.path.isdir(rootDir):
					rootItem = QStandardItem(os.path.basename(rootDir))
					setattr(rootItem, 'rootDir', rootDir)
					self.appendRow(rootItem)
					self.AddLayer(rootDir, rootItem, bSettingUp=True)
	
	def AddLayer(self, dir, parentItem, layerNum=2, bSettingUp=False):
		"""Add a layer to the filesystem, if it doesn't exist already. Works in pairs of two layers, to create branch symbols even for branches the user hasn't traversed yet."""
		if bSettingUp or parentItem not in self.processedLayers:
			if layerNum == 2:
				#print('PROCESS', dir)   # TODO: Remove.
				self.processedLayers.append(parentItem)
				if not bSettingUp:
					# We know that wherever we are, we already made a layer of children; populate that layer, now.
					for i in range(parentItem.rowCount()):
						item = parentItem.child(i, 0)
						self.AddLayer(os.path.join(dir, item.text()), item, layerNum - 1, bSettingUp)
			if bSettingUp or layerNum == 1:
				for name in os.listdir(dir):
					if os.path.isdir(os.path.join(dir, name)):
						item = QStandardItem(name)
						parentItem.appendRow(item)
						if layerNum > 1:
							self.AddLayer(os.path.join(dir, name), item, layerNum - 1, bSettingUp)
	
	def AllowExpandLayer(self, index):
		"""Call this with an appropriate index whenever a branch of the tree is expanded. It creates the necessary items for the filesystem model, layer by layer (to prevent slowdown by scanning the whole library structure at once)."""
		dir, parentItem = self.dir(index, bReturnItem=True)
		self.AddLayer(dir, parentItem)
	
	def dir(self, index, bReturnItem=False):
		"""Get the dir (and, optionally, the item) at a particular clicked index point."""
		item = origItem = self.itemFromIndex(index)
		if item is None:   # Say the user just clicked on some spot in the tree view which didn't have an item located there.
			return None
		dir = item.text()
		if hasattr(item, 'rootDir'):
			if self.bUseRootBaseName:
				dir = os.path.join(getattr(item, 'rootDir'), dir)
			else:
				dir = getattr(item, 'rootDir')
		else:
			while item.parent() is not None:   # Unless we failed to set a root dir, we should break before the end condition, anyway.
				item = item.parent()
				if hasattr(item, 'rootDir'):
					if self.bUseRootBaseName:
						dir = os.path.join(os.path.join(getattr(item, 'rootDir'), item.text()), dir)
					else:
						dir = os.path.join(getattr(item, 'rootDir'), dir)
					break
				else:
					dir = os.path.join(item.text(), dir)
			if not hasattr(item, 'rootDir'):   # We never found a root dir.
				raise LogicError('Failed to get a full path for tree item dir.')
		if bReturnItem:
			return dir, origItem
		return dir