# Standard interface imports
#
# Notes:
#  Imports the standard things for an interface to import. You can just import everything from
# this file to automate the process.

import sys, os, random

try:
	import configparser
except ImportError:
	import ConfigParser as configparser

from qt import *
from util import LogicError, ConfigValueError, PathNotExistError, SQ
from constants import *
import gbl
from gbl import ResetCurrentTrackRow, BLibraryChanged, AcceptCurrentLibrary
from kea_util import ShowWarning, ShowRestartChangesMessage, RunStdInterface, RunShapedInterface, GetImgDir, CreateStdHotkeys, GetTableDB, StripOrderBy, InsertDirSearchIntoQuery, InsertWordSearchIntoQuery, DrawPixmap, GetAlbumArtFromDir, GetHoverButton, GetHoverButtonData, GetHoverButtonIconData
from tags import GetFileTags
from db import GetLibraryDirs
from walker import RemoveFileFromDatabase, SetLibraryChangedCallback
from config import GetConfigFile, GetConfigValues, WriteConfigFile
#from watcher import StartWatchDirs, EndWatchDirs   # This triggers the watcher.
from hotkeys import CreateGlobalHotkey, CreateGlobalWin32Hotkey, DeleteGlobalHotkeys, DeleteGlobalWin32Hotkeys