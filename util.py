# Generally non-kea-specific utility functions
#
# Notes:
#  Since this is widely imported by other modules, it has to keep imports to a minimum.


import sys, os, platform
import gbl


#  ----------
# --- Errors
#  ----------

class SepException(Exception):
	"""A custom exception class that allows multiple arguments."""
	def __init__(self, *data, **kw_args):
		self.sep = kw_args.get('sep', ' ')
		try:
			self.args = self.data = [str(e) for e in data]
		except UnicodeEncodeError as error:
			try:
				self.args = self.data = [unicode(e) for e in data]   # See if the problem was Python 2's non-Unicode str class.
			except NameError:   # No Python 2 Unicode class exists.
				raise error
	def __str__(self):
		return self.sep.join(self.data)
	def __repr__(self):
		return self.sep.join(self.data)
	def message(self):
		return self.__str__()

'''class FatalError(SepException):
	pass'''
class LogicError(SepException):
	pass
'''class SetupError(SepException):
	pass'''
class RequiredImportError(SepException):
	pass

'''class PathExistsError(SepException):
	pass'''
class PathNotExistError(SepException):
	pass
'''class PathCreateError(SepException):
	pass'''

class InterfaceSetupError(SepException):
	pass

'''class ConfigSectionError(SepException):
	pass
class ConfigOptionError(SepException):
	pass'''
class ConfigValueError(SepException):
	pass


#  --------------------
# --- Operating System
#  --------------------

def BOnWindows():
	return platform.system() == 'Windows' or platform.system() == 'Microsoft'
def BOnMac():
	return platform.system() == 'Darwin'
def BOnLinux():
	return platform.system() == 'Linux'
def BOnUnix():
	return BOnMac() or BOnLinux()   # Not technically exact, terminologically.


#  ----------
# --- Python
#  ----------

def BPython2():
	return sys.version_info[0] == 2
def BPython3():
	return sys.version_info[0] == 3


#  ---------
# --- Types
#  ---------

def BInt(text):
	try:
		int(text)
		return True
	except (ValueError, TypeError, AttributeError):   # Attribute error for no __float__.
		return False

def BNumber(text):
	try:
		float(text)
		return True
	except (ValueError, TypeError, AttributeError):   # Attribute error for no __float__.
		return False


#  -----------
# --- Strings
#  -----------

def SQ(*args, **kw_args):
	"""Wrap the arguments in single quotes."""
	sep = kw_args.get('sep', ' ')
	rval = "'"
	for i in range(len(args)):
		try:
			rval = rval + str(args[i])
		except UnicodeEncodeError as error:
			try:
				rval = rval + unicode(args[i])   # See if the problem was Python 2's non-Unicode str class.
			except NameError:   # No Python 2 Unicode class exists.
				raise error
		if sep != '' and i < len(args) - 1:
			rval = rval + sep
	return rval + "'"

def Colonize(string):
	"""Return a copy of the string with a colon after it."""
	try:
		return string + ':'
	except TypeError:
		try:
			return str(string) + ':'
		except UnicodeEncodeError as error:
			try:
				return unicode(string) + ':'   # See if the problem was Python 2's non-Unicode str class.
			except NameError:   # No Python 2 Unicode class exists.
				raise error

# Possibly TODO: Allow a bool to stipulate whether to shorten replacements; for example, ShortenPath("123456789", 8) to yield 12345678. instead of 12345...
def ShortenStr(string, maxLength, side, replacement = '...'):  #, bShortenReplacement = False
	"""Shortens a string to a desired length, plus '...' or a similar replacement string. Pass in 'left', 'front', 'l', or 'f' to shorten the front of the string, 'right', 'back', 'r', 'or 'b' to shorten the back."""
	if len(string) > maxLength:
		if side == 'left' or side == 'l' or side == 'front' or side == 'f':
			string = string[min( len(string) - maxLength + len(replacement), len(string) ) :]
			
			if replacement != '':
				string = replacement[: min(maxLength, len(replacement))] + string
		
		elif side == 'right' or side == 'r' or side == 'back' or side == 'b':
			string = string[: len(string) - min( len(string) - maxLength + len(replacement), len(string) )]
			
			if(replacement != ''):
				string += replacement[: min(maxLength, len(replacement))]
		
		else:
			raise ArgTextError('Invalid side (front/back) argument.')
	
	return string

def ShortenPath(string, maxLength=gbl.shortPathLength):
	"""Shorten a path to be printable."""
	return ShortenStr(string, maxLength, 'f', '...')

def SlashedDir(dir):
	"""Utility function that ensures that a dir path ends with a slash."""
	return dir if dir.endswith('/') else dir + '/'


#  ---------
# --- Files
#  ---------

def FileChoice(path1, path2):
	if os.path.isfile(path1):
		return path1
	elif os.path.isfile(path2):
		return path2
	else:
		return None