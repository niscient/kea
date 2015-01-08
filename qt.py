# Qt library
#
# Notes:
#   There's no performance penalty for importing all Qt modules into whichever modules
#  need access to at least some Qt modules, so for simplicity's sake that's what we'll do.


from util import RequiredImportError
from constants import PYSIDE, PYQT4
import qt_helper


_qtLib = qt_helper.qtLib

def QtLib():
	"""Returns PYSIDE or PYQT4, whichever is being used by the program."""
	return _qtLib

if _qtLib == PYSIDE:
	from PySide import QtGui, QtCore, QtSql
	from PySide.QtGui import *
	from PySide.QtCore import *
	from PySide.QtSql import *
	from PySide.phonon import Phonon
elif _qtLib == PYQT4:
	import sip
	sip.setapi('QString', 2)   # Prevent QString from being returned by PyQt4 functions.
	sip.setapi('QVariant', 2)   # Prevent QVariant from being returned by PyQt4 functions.
	from PyQt4 import QtGui, QtCore, QtSql
	from PyQt4.QtGui import *
	from PyQt4.QtCore import *
	from PyQt4.QtSql import *
	from PyQt4.phonon import Phonon
else:
	raise RequiredImportError('No Qt library found.')