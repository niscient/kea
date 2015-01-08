# Standard shaped main window base class
#
# Notes:
#  Inherit from this or use it directly to implement a shaped main window.
#   The moveEvent and resizeEvent shells need to exist or custom overrides of them from a widget
#  class won't work. This is somewhat strange, but it seems to be how Qt works.
#
# To do:
#  Make a subclass that can be resized.


#!/usr/bin/env python

import sys, os

from qt import *
import gbl
from gbl import FixGarbageCollection
from kea_util import DrawPixmap
from std_main_menu import StdMainMenu


class ShapedMainWindowBase(QMainWindow):
	"""Shaped main window base class. Uses an image as a background. You can draw foreground elements either by adding them to a list of drawn elements or by using standard labels and such."""
	
	def __init__(self, bgImgPath, x, y, mainWidgetClass, bShow=True):
		super(ShapedMainWindowBase, self).__init__()
		
		self.setWindowTitle(gbl.programName)
		
		self.mainMenu = StdMainMenu(self, QMenu(self))
		
		if mainWidgetClass is not None:
			self.mainWidget = mainWidgetClass(self)   # The main widget class should take 'parent' as its first argument.
			self.setCentralWidget(self.mainWidget)
		
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_TranslucentBackground)
		
		self.pixmap = QPixmap(bgImgPath)
		width = self.pixmap.width()
		height = self.pixmap.height()
		self.setGeometry(x, y, width, height)
		
		color = QColor(0, 0, 0, 0)
		pixmap = QPixmap(QSize(width, height))
		pixmap.fill(color)
		
		rect = QRectF(0.0, 0.0, width, height)
		painter = QPainter()
		painter.begin(pixmap)
		painter.setRenderHints(QPainter.Antialiasing, True)
		painter.end()
		
		self.setMask(self.pixmap.mask())   # For Linux.
		
		self.drawPixmaps = []
		
		self.mouseOffset = None   # Used to keep track of mouse press position, for window dragging. Will be set before it's used.
		
		if bShow:
			self.show()
		
		FixGarbageCollection(self)
	
	def moveEvent(self, event):
		super(ShapedMainWindowBase, self).moveEvent(event)
	
	# TODO something: This currently won't be used for much, since there's no resizable shaped window class right now.
	def resizeEvent(self, event):
		super(ShapedMainWindowBase, self).resizeEvent(event)
	
	def sizeHint(self):
		return QSize(self.pixmap.width(), self.pixmap.height())
	
	def paintEvent(self, event):
		painter = QPainter(self)
		painter.drawTiledPixmap(self.rect(), self.pixmap)
		for drawPixmap in self.drawPixmaps:
			painter.drawPixmap(drawPixmap.x, drawPixmap.y, drawPixmap.width, drawPixmap.height, drawPixmap.pixmap)
		super(ShapedMainWindowBase, self).paintEvent(event)
		#print('(redraw)')   # TODO remove
	
	def contextMenuEvent(self, event):
		self.ShowMainMenu(event.globalPos())
	
	def mousePressEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			self.mouseOffset = event.pos()
		else:
			self.mouseOffset = None
		super(ShapedMainWindowBase, self).mousePressEvent(event)
	
	def mouseReleaseEvent(self, event):
		self.mouseOffset = None
		super(ShapedMainWindowBase, self).mouseReleaseEvent(event)
	
	def mouseMoveEvent(self, event):
		if self.mouseOffset is not None:
			self.move(event.globalX() - self.mouseOffset.x(), event.globalY() - self.mouseOffset.y())
		super(ShapedMainWindowBase, self).mouseMoveEvent(event)
	
	def ShowMainMenu(self, pos):
		self.mainMenu.menu.exec_(pos)
	
	def AddDrawPixmap(self, pixmapOrImgPathOrDrawPixmap, x=None, y=None):
		"""Adds a pixmap, DrawPixmap, or image path to the draw pixmap list as a DrawPixmap. Supply x and y arguments unless adding a DrawPixmap."""
		if isinstance(pixmapOrImgPathOrDrawPixmap, DrawPixmap):
			self.drawPixmaps.append(pixmapOrImgPathOrDrawPixmap)
		else:
			self.drawPixmaps.append(DrawPixmap(pixmapOrImgPath, x, y))