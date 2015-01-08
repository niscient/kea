# Standard progress bar
#
# Notes:
#   


from qt import *


class StdProgressBar(QFrame):
	def __init__(self, parent, x, y, width, height, player, progressBarStyle=None):
		"""Create a progress bar. Note: 'player' should be a StdPlayer object."""
		super(StdProgressBar, self).__init__(parent)
		self.setGeometry(x, y, width, height)
		self.setStyleSheet('QFrame { background-color: transparent; }')
		
		progressBar = Phonon.SeekSlider(player.player, self)
		progressBar.setMediaObject(player.player)
		if progressBarStyle is not None:
			progressBar.setStyleSheet(progressBarStyle)
		
		layout = QHBoxLayout()
		layout.addWidget(progressBar)
		self.setLayout(layout)