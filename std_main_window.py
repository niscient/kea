# Standard main window
#
# Notes:
#  A version of the standard main window base class which uses config files.
#
# Config file usage:
#   Program->x, y, width, height
#   Program->bRemoveSingleTreeRootNode: Stores whether the tree node will display a solo root
#  node, or whether it'll only display its contents.


from qt import Qt
from std_main_window_base import StdMainWindowBase


class StdMainWindow(StdMainWindowBase):
	def __init__(self, x, y, w, h, bMaximized, mainWidgetClass, configFile, bShow=True):
		self.configFile = configFile
		super(StdMainWindow, self).__init__(x, y, w, h, bMaximized, mainWidgetClass, bShow)
	
	def moveEvent(self, event):
		bMaximized = self.windowState() & Qt.WindowMaximized
		if not bMaximized:
			self.configFile.set('Program', 'x', str(event.pos().x()))
			self.configFile.set('Program', 'y', str(event.pos().y()))
		super(StdMainWindow, self).moveEvent(event)
	
	def resizeEvent(self, event):
		if self.windowState() & Qt.WindowMaximized:
			self.configFile.set('Program', 'bMaximized', str(True))
		else:
			self.configFile.set('Program', 'bMaximized', str(False))
			self.configFile.set('Program', 'width', str(event.size().width()))
			self.configFile.set('Program', 'height', str(event.size().height()))
		super(StdMainWindow, self).resizeEvent(event)