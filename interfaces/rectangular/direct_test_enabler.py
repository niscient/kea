# Interface direct test enabler
# (put a copy this file in each interface's directory)
#
# Notes:
#  A special module which can make a module independently runnable (rather than running it through
# the main program), for testing purposes. (This only applies when dealing with the source code,
# not with a frozen, platform-specific version of the program. But it's still a time-saver to
# run an interface file directly rather than run it through the main kea module.)
#  To use this module, a copy of it should be placed in an interface's directory and imported in
# that interface's module, if, in that module, __name__ == '__main__'. This import must be done
# before the 'gbl' module, any module which imports it, or indeed any normal kea module at all is
# imported (so that these modules can be found in the first place).


import sys, os


# If we're using an IDE, it might use an absolute path for the command-line argument.
_bAbsolutePath = os.path.isabs(sys.argv[0])
if _bAbsolutePath:
	_programDir = os.path.dirname(os.path.dirname(os.path.dirname(sys.argv[0])))
else:
	_interfacePathNoExt = os.path.splitext(os.path.join(os.getcwd(), sys.argv[0]))[0]
	_programDir = os.path.dirname(os.path.dirname(os.path.dirname(_interfacePathNoExt)))
if len(_programDir) > 0:
	if _programDir not in sys.path:
		sys.path.insert(0, _programDir)
	os.chdir(_programDir)
	
	import gbl_helper
	gbl_helper.programDir = _programDir
	gbl_helper.interfaceName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
	
	if _bAbsolutePath:
		gbl_helper.interfacePathNoExt = os.path.splitext(sys.argv[0])[0]
	else:
		gbl_helper.interfacePathNoExt = _interfacePathNoExt