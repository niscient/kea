# Standard shaped main window
#
# Notes:
#  A version of the shaped main window base class which uses config files.
#
# Config file usage:
#   Program->x, y


from shaped_main_window_base import ShapedMainWindowBase


class ShapedMainWindow(ShapedMainWindowBase):
	def __init__(self, bgImgPath, x, y, mainWidgetClass, configFile, bShow=True):
		self.configFile = configFile
		super(ShapedMainWindow, self).__init__(bgImgPath, x, y, mainWidgetClass, bShow)
	
	def moveEvent(self, event):
		self.configFile.set('Program', 'x', str(event.pos().x()))
		self.configFile.set('Program', 'y', str(event.pos().y()))
		super(ShapedMainWindow, self).moveEvent(event)
	
	# TODO: Remove? Depends on future extension of this class.
	'''def resizeEvent(self, event):
		self.configFile.set('Program', 'width', str(event.size().width()))
		self.configFile.set('Program', 'height', str(event.size().height()))
		super(ShapedMainWindow, self).resizeEvent(event)'''