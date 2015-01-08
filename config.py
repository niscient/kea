# Config file reader
#
# Notes:
#   Reads INI files, usually only the one associated with the current interface.
#
#   Each interface should be created as a named folder inside the 'interfaces' directory. Inside
#  the named folder should be a .py file of the same name, which will be treated as that
#  interface's main program file, and an .ini file of the same name, which will be used to store
#  that interface's configuration data. There will also be another .ini file, of the same name as
#  the main .ini file but followed by the string '_reset'. Since user-activated changes to the way
#  an interface works are stored in the main interface, any attempt to reset the interface to its
#  default state will overwrite the main .ini file with this reset file.
#
#   Additionally, on Python 2, empty files named __init__.py must be placed in the 'interfaces'
#  dir as well as each of the actual dirs used by the interfaces.


import os, shutil

try:
	import configparser
except:
	import ConfigParser as configparser

from util import InterfaceSetupError, PathNotExistError, SQ
import gbl


def GetDefaultInterfaceName():
	if not os.path.isfile(gbl.configPath):
		raise PathNotExistError(gbl.configPath)
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(gbl.configPath)
	return config.get('Program', 'interface')

def SetDefaultInterfaceName(interfaceName):
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(gbl.configPath)
	config.set('Program', 'interface', interfaceName)
	with open(gbl.configPath, 'w') as outFile:
		config.write(outFile)

def GetInterfaceList():
	config = configparser.ConfigParser(allow_no_value=True)
	
	# Prevent option names from coming back always in lower case.
	try:
		config.optionxform = unicode
	except NameError:
		config.optionxform = str
	
	config.read(gbl.configPath)
	interfaceNames = dict(config.items('Interfaces')).keys()
	return interfaceNames

def GetConfigValues(configObj, section, *args):
	"""Given a config file object, get values for a series of same-section config options (keys). Pass these options in as arguments."""
	values = []
	for arg in args:
		values.append(configObj.get(section, arg))
	return values

def GetStandardWindowSetup(configObj, bShapedWindow=False):
	"""Get x, y, width, height, and, possibly, bMaximized values from a config file object."""
	if bShapedWindow:
		return GetConfigValues(configObj, 'Program', 'x', 'y')
	else:
		return GetConfigValues(configObj, 'Program', 'x', 'y', 'width', 'height', 'bMaximized')

def GetConfigFilePath():
	"""This will return the path of the current interface's config file."""
	if gbl.interfacePathNoExt is None:
		raise InterfaceSetupError('Interface doesn\'t set up extensionless path.')
	configPath = gbl.interfacePathNoExt + gbl.configExt
	if not os.path.isfile(configPath):
		raise PathNotExistError(configPath)
	return configPath

def GetConfigFile():
	"""This will return a ConfigParser object which uses the current interface's config file."""
	config = configparser.ConfigParser()
	
	# Prevent option names from always being stored in lower case.
	try:
		config.optionxform = unicode
	except NameError:
		config.optionxform = str
	
	configPath = GetConfigFilePath()
	if not os.path.isfile(configPath):
		raise PathNotExistError(configPath)
	config.read(configPath)
	return config

def WriteConfigFile(configObj):
	"""Pass in a ConfigParser object. This will write the contents of the ConfigParser object to the current interface's config file."""
	with open(GetConfigFilePath(), 'w') as outFile:
		configObj.write(outFile)

def ResetConfigFile():
	"""This will overwrite the contents of the current interface's config file with the config backup file."""
	configPath = GetConfigFilePath()
	# Note that GetConfigFilePath() already checked if the no-extension path existed.
	configBackupPath = gbl.interfacePathNoExt + gbl.configBackupSuffix + gbl.configExt
	if not os.path.isfile(configBackupPath):
		raise PathNotExistError(configBackupPath)
	shutil.copyfile(configBackupPath, configPath)