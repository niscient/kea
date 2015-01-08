# kea
# Rains Jordan
#
# Notes:
#  The main file for kea. Runs the default interface.
#  Currently only supports Python 2.


#!/usr/bin/env python
from __future__ import absolute_import
import sys, os, importlib

try:
	import configparser
except:
	import ConfigParser as configparser

from qt import *
from util import InterfaceSetupError, ConfigValueError, BOnLinux, SQ, ShortenPath
import gbl
from kea_util import ShowError
import db
from config import GetDefaultInterfaceName

if __name__ == '__main__':
	try:
		if BOnLinux():
			#  PyQt4 seems to have a bug that leads to this message appearing: "(python:xxxx): Gtk-CRITICAL **: IA__gtk_widget_style_get: assertion 'GTK_IS_WIDGET (widget)' failed"
			#  Further details: https://bugs.launchpad.net/ubuntu/+source/qt4-x11/+bug/805303
			#  We can run "export LIBOVERLAY_SCROLLBAR=0" to prevent this problem.
			os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
		
		if not os.path.isfile(gbl.configPath):
			raise InterfaceSetupError('Config file doesn\'t exist:', SQ(ShortenPath(gbl.configPath)))
		interfaceName = GetDefaultInterfaceName()
		if interfaceName is None:
			raise InterfaceSetupError('No default interface supplied.')
		interfaceDir = os.path.join(gbl.interfacesDir, interfaceName)
		if not os.path.isdir(interfaceDir):
			raise InterfaceSetupError('Invalid interface:', SQ(interfaceName))
		
		# Even though the interface can really choose what config files it wants to use, we'll
		# mandate the existence of standard config and config backup files to create a standard
		# format.
		configPath = os.path.join(interfaceDir, interfaceName + gbl.configExt)
		if not os.path.isfile(configPath):
			raise InterfaceSetupError('Config file doesn\'t exist:', SQ(ShortenPath(configPath)))
		configBackupPath = os.path.join(interfaceDir, interfaceName + gbl.configBackupSuffix + gbl.configExt)
		if not os.path.isfile(configBackupPath):
			raise InterfaceSetupError('Backup config file doesn\'t exist:', SQ(ShortenPath(configBackupPath)))
		
		if not os.path.isdir(gbl.interfacesDir):
			raise InterfaceSetupError('No \'{}\' dir.'.format(gbl.interfacesDir))
		interfaceModuleStr = '{}.{}.{}'.format(gbl.interfacesDirImport, interfaceName, interfaceName)
		gbl.interfaceName = interfaceName
		gbl.interfacePathNoExt = os.path.join(os.path.join(gbl.interfacesDir, interfaceName), interfaceName)
		gbl.interfaceDir = os.path.dirname(gbl.interfacePathNoExt)
		module = importlib.import_module(interfaceModuleStr)
		
		# Note: If the interface doesn't have a main function, we'll just leave it to its own devices. (It may have global-scope code that's executed automatically.)
		if hasattr(module, 'main'):
			module.main()
	except (configparser.NoSectionError, configparser.NoOptionError) as err:
		ShowError(SQ(gbl.interfaceName) + ':\n\nConfig file error:\n' + str(err))
	except ConfigValueError as err:
		ShowError(SQ(gbl.interfaceName) + ':\n\nConfig value error:\n' + SQ(str(err)))
	except KeyError as err:
		ShowError(SQ(gbl.interfaceName) + ':\n\nKey value error:\n' + str(err))
	except Exception as err:
		if len(gbl.interfaceName) > 0:
			ShowError(SQ(gbl.interfaceName) + ':\n\n' + str(err))
		else:
			ShowError(str(err))
		# TODO remove
		#import traceback
		#traceback.print_exc(file=sys.stdout)