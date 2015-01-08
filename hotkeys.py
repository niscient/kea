# Global hotkeys
#
# Notes:
#   PyGlobalShortcut (which internally uses libqxt's QxtGlobalShortcut) is used for global
#  hotkeys, but its coverage is spotty. It doesn't seem to support the Numpad keys, for
#  example. So I've introduced a Win32 system as an alternative.
#   Both systems currently only support PyQt, not PySide. For the Win32 system, this is
#  because PySide inexplicably lacks QAbstractEventDispatcher.setEventFilter().
#
# To do:
#	Test PyGlobalShortcut's Linux and Mac support, particularly with the numpad.


from __future__ import print_function
from qt import QtLib, PYSIDE, PYQT4


#  --------------------
# --- PyGlobalShortcut
#  --------------------

from qt import QKeySequence
try:
	from pygs import QxtGlobalShortcut
except ImportError:
	pass   # Do nothing, but the user will get other errors if they try to make global hotkeys using PyGlobalShortcut.

_shortcuts = []

def CreateGlobalHotkey(keyCombo, func):
	"""Create a global hotkey, connecting a callback function to a key or key combination (example: "Ctrl+Z"). A global hotkey can be created after an application has started running, but it must be created after the application has been created. Returns whether a global hotkey was set up or not."""
	if QtLib() == PYQT4:
		shortcut = QxtGlobalShortcut()
		shortcut.setShortcut(QKeySequence(keyCombo))
		shortcut.activated.connect(func)
		_shortcuts.append(shortcut)
		return True
	return False

def SetUpGlobalHotkey(keyCombo, func, fallBackParent=None):
	"""Sets up a global hotkey. Takes a textual key combinations and a callback function. If it fails to set up a global hotkey and a parent object is provided, it at least hooks a new non-global shortcut up to the parent object. It never tries the Win32 method."""
	if not CreateGlobalHotkey(keyCombo, func):
		# At least make a non-global hotkey.
		if fallBackParent is not None:
			QShortcut(QKeySequence(keyCombo), fallBackParent, func)

def SetUpGlobalHotkeys(globalHotkeys, fallBackParent=None):
	"""Sets up global hotkeys. Takes a dictionary with textual key combinations as keys and callback functions as values. If it fails to set up some global hotkeys and a parent object is provided, it at least hooks new non-global shortcuts up to the parent object. It never tries the Win32 method."""
	for keyCombo, func in globalHotkeys.items():
		if not CreateGlobalHotkey(keyCombo, func):
			# At least make a non-global hotkey.
			if fallBackParent is not None:
				QShortcut(QKeySequence(keyCombo), fallBackParent, func)

def DeleteGlobalHotkeys():
	"""Delete the global hotkeys created through CreateGlobalHotkey(). Should be run at the end of your program."""
	for shortcut in _shortcuts:
		del shortcut


#  ---------
# --- Win32
#  ---------

import ctypes	 # TODO: Strangely, this import is unnecessary, while the ctypes.wintypes one is.

from util import BOnWindows
if BOnWindows():
	import ctypes.wintypes

from qt import QApplication, QAbstractEventDispatcher
from constants import WM_HOTKEY

_win32Hotkeys = {}

def CreateGlobalWin32Hotkey(vk, modifiers, func):
	"""Create a global Win32 hotkey, connecting a callback function to a key or key combination given through Win32 virtual key and modifier codes. A global Win32 hotkey can be created either before or after an application has been created. Returns whether a global hotkey was set up or not."""
	if not BOnWindows():
		return False
	if QtLib() == PYSIDE:
		return False   # There's currently no way to detect WM_HOTKEY events on PySide, so let's not even bother.
	id = len(_win32Hotkeys) + 1
	if ctypes.windll.user32.RegisterHotKey(None, id, modifiers, vk):
		_win32Hotkeys[id] = func
		return True
	else:
		return False

# TODO either remove or make this work, maybe even make a multiple-args version. Gotta get a keyCombo from the VK though.
'''
def SetUpGlobalWin32Hotkey(vk, modifiers, func, fallBackParent=None):
	"""Sets up a global Win32 hotkey. Takes a Win32 virtual key, Win32 modifier code, and a callback function. If it fails to set up a global hotkey and a parent object is provided, it at least hooks a new non-global shortcut up to the parent object."""
	if not CreateGlobalWin32Hotkey(vk, modifiers, func):
		# At least make a non-global hotkey.
		if fallBackParent is not None:
			QShortcut(QKeySequence(keyCombo), fallBackParent, func)
'''

def DeleteGlobalWin32Hotkeys():
	"""Delete the global hotkeys created through CreateGlobalWin32Hotkey(). Should be run at the end of your program."""
	for id in _win32Hotkeys.keys():
		ctypes.windll.user32.UnregisterHotKey(None, id)

def GlobalWin32HotkeysEventFilter(msg):
	if int(msg.message) == WM_HOTKEY:
		func = _win32Hotkeys.get(msg.wParam)
		if func is not None:
			func()
			return True
	return False

class GlobalWin32HotkeysApplication(QApplication):
	def __init__(self, *args):
		super(GlobalWin32HotkeysApplication, self).__init__(*args)
		if QtLib() == PYQT4 and BOnWindows():
			QAbstractEventDispatcher.instance().setEventFilter(GlobalWin32HotkeysEventFilter)
