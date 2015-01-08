# Standard main window base class
#
# Notes:
#  Inherit from this or use it directly to implement a standard window.
#   The moveEvent and resizeEvent shells need to exist or custom overrides of them from a widget
#  class won't work. This is somewhat strange, but it seems to be how Qt works.


#!/usr/bin/env python

import sys, os, webbrowser

from qt import *
import gbl
from gbl import FixGarbageCollection
from std_main_menu import StdMainMenu


class StdMainWindowBase(QMainWindow):
	def __init__(self, x, y, w, h, bMaximized, mainWidgetClass, bShow=True):
		super(StdMainWindowBase, self).__init__()
		
		self.setGeometry(x, y, w, h)
		self.setWindowTitle(gbl.programName)
		
		self.mainMenu = StdMainMenu(self, self.menuBar())
		self.menuBar().setStyleSheet('QMenuBar { font-size: 8pt; font-weight: bold; }')
		
		if mainWidgetClass is not None:
			self.mainWidget = mainWidgetClass(self)   # The main widget class should take 'parent' as its first argument.
			self.setCentralWidget(self.mainWidget)
		
		if bShow:
			if bMaximized:
				self.showMaximized()
			else:
				self.show()
		
		FixGarbageCollection(self)
	
	def moveEvent(self, event):
		super(StdMainWindowBase, self).moveEvent(event)
	
	def resizeEvent(self, event):
		super(StdMainWindowBase, self).resizeEvent(event)