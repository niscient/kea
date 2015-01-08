# Image-based horizontal or vertical volume bar
#
# Notes:
#   


from qt import *


class ImgVolumeBar(QFrame):
	"""An image-based volume bar, which you can drag from empty to full along either the horizontal or vertical axis (but not both)."""
	
	def __init__(self, parent, bgImgPath, fillImgPath, bVertical=True, bFlipped=False, startingPercent=1):
		"""Provide the parent, background image path, and fill image path (which is used for the size of the drawing frame). You can use bVertical to set whether the bar is vertical, and bFlipped to set whether the bar should fill from bottom/left to top/right (default) or top/right to bottom/left (by setting bFlipped to True). You can also supply a starting percent (from 0 to 1)."""
		super(ImgVolumeBar, self).__init__(parent)
		self.parent = parent
		
		self.bg = QLabel(self)
		self.bg.setPixmap(QPixmap(bgImgPath))
		#self.bg.setStyleSheet('background: transparent;')   # TODO: Remove.
		
		self.fillPixmap = QPixmap(fillImgPath)
		self.resize(self.fillPixmap.size())
		
		self.bVertical = bVertical
		self.bFlipped = bFlipped
		
		if bVertical:
			self.drawWidth = self.fillPixmap.width()
			self.drawHeight = int(startingPercent * self.fillPixmap.height())
		else:
			self.drawWidth = int(startingPercent * self.fillPixmap.width())
			self.drawHeight = self.fillPixmap.height()
		
		self.volumeChangedCallback = None
	
	def paintEvent(self, event):
		painter = QPainter()
		painter.begin(self)
		
		# TODO maybe reuse: this is a very cool little stretch effect
		#painter.drawPixmap(QRectF(0, 0, self.fillPixmap.width(), self.fillPixmap.height()), self.fillPixmap, QRectF(0, self.fillPixmap.height() - self.drawHeight, self.fillPixmap.width(), self.drawHeight))
		
		if self.bVertical:
			if self.bFlipped:   # Fill from top to bottom.
				rect = QRectF(0, 0, self.drawWidth, self.drawHeight)
			else:   # Fill from bottom to top.
				rect = QRectF(0, self.fillPixmap.height() - self.drawHeight, self.drawWidth, self.drawHeight)
		else:
			if self.bFlipped:   # Fill from right to left.
				rect = QRectF(self.fillPixmap.width() - self.drawWidth, 0, self.drawWidth, self.drawHeight)
			else:   # Fill from left to right.
				rect = QRectF(0, 0, self.drawWidth, self.drawHeight)
		
		painter.drawPixmap(rect, self.fillPixmap, rect)
		
		painter.end()
	
	def mousePressEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			if self.bVertical:
				y = event.pos().y()
				drawY = y
				
				if self.bFlipped:
					volumePercent = y / (self.fillPixmap.height() - 1.0)
					self.drawHeight = drawY
				else:
					volumePercent = (self.fillPixmap.height() - 1.0 - y) / (self.fillPixmap.height() - 1)
					self.drawHeight = self.fillPixmap.height() - drawY
				#print(y, volumePercent, drawY)   # TODO remove
			else:
				x = event.pos().x()
				drawX = x
				
				if self.bFlipped:
					volumePercent = (self.fillPixmap.width() - 1.0 - x) / (self.fillPixmap.width() - 1)
					self.drawWidth = self.fillPixmap.width() - drawX
				else:
					volumePercent = x / (self.fillPixmap.width() - 1.0)
					self.drawWidth = drawX
				#print(x, volumePercent, drawX)   # TODO remove
			
			self.repaint()
			if self.volumeChangedCallback is not None:
				self.volumeChangedCallback(volumePercent)
			
			#super(ImgVolumeBar, self).mousePressEvent(event)   # No need for this, so we won't do it.
	
	def mouseMoveEvent(self, event):
		# Nicely enough, Qt does most of the work here for us; it'll keep on sending the "drag" event even after the mouse moves away, as long as the button is still down.
		if event.buttons() & Qt.LeftButton:
			if self.bVertical:
				y = event.pos().y()
				drawY = y
				if y < 0:
					y = 0
					drawY = 0
				if y >= self.fillPixmap.height():
					y = self.fillPixmap.height() - 1
					drawY = self.fillPixmap.height()
				
				if self.bFlipped:
					volumePercent = y / (self.fillPixmap.height() - 1.0)
					self.drawHeight = drawY
				else:
					volumePercent = (self.fillPixmap.height() - 1.0 - y) / (self.fillPixmap.height() - 1)
					self.drawHeight = self.fillPixmap.height() - drawY
				#print(y, volumePercent, drawY)   # TODO remove
			else:
				x = event.pos().x()
				drawX = x
				if x < 0:
					x = 0
					drawX = 0
				if x >= self.fillPixmap.width():
					x = self.fillPixmap.width() - 1
					drawX = self.fillPixmap.width()
				
				if self.bFlipped:
					volumePercent = (self.fillPixmap.width() - 1.0 - x) / (self.fillPixmap.width() - 1)
					self.drawWidth = self.fillPixmap.width() - drawX
				else:
					volumePercent = x / (self.fillPixmap.width() - 1.0)
					self.drawWidth = drawX
				#print(x, volumePercent, drawX)   # TODO remove
			
			self.repaint()
			if self.volumeChangedCallback is not None:
				self.volumeChangedCallback(volumePercent)
			
			#super(ImgVolumeBar, self).mouseMoveEvent(event)   # Commented out to prevent the window-dragging mechanism from activating.
	
	def SetVolumeChangedCallback(self, func):
		"""Set a callback function to be run when the volume is changed. It must take a volume percent (from 0 to 1) as an argument."""
		self.volumeChangedCallback = func
	
	def SetBGPos(self, x, y):
		self.bg.move(x, y)
	
	def SetFillPos(self, x, y):
		self.fill.move(x, y)
	
	def SetPercent(self, volumePercent):
		if volumePercent > 1:
			volumePercent = 1
		elif volumePercent < 0:
			volumePercent = 0
		
		if self.bVertical:
			self.drawWidth = self.fillPixmap.width()
			self.drawHeight = int(volumePercent * self.fillPixmap.height())
		else:
			self.drawWidth = int(volumePercent * self.fillPixmap.width())
			self.drawHeight = self.fillPixmap.height()
		self.repaint()