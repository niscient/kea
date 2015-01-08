# cx_Freeze build script
#
# Notes:
#   Windows only: When running the built executable, you will have problems with Qt not being able
#  to find its SQL drivers. To fix this, copy the sqldrivers directory from your Python
#  installation's site-packages/PySide/plugins directory (or the PyQt4 equivalent) into the
#  directory that contains your built executable. (To be exact, the only DLL you need from the
#  sqldrivers dir is qsqlite4.) You'll also have trouble loading JPG and GIF album art. Copy the
#  PySide or PyQt imageformats directory (also located in plugins) to the .exe directory to fix
#  this. (You'll probably only need qjpeg4.dll, since most album art is PNG or JPG.)
#   Windows only, when using hsaudiotag: Some old versions of cx_Freeze have a bug that makes them
#  unable to find the hsaudiotag zipped .egg file. To fix this, unzip the .egg file (it's just a
#  renamed .zip file), and make a copy of the 'hsaudiotag' subdir that exists alongside the
#  'EGG-INFO' subdir. Use pip or another method to uninstall your normal version of hsaudiotag,
#  removing the .egg file. Then put your copied 'hsaudiotag' subdir into either your Python
#  installation's site-packages directory or in the kea directory, alongside this setup file.
#   You will also need to put kea.ini and the 'interfaces' dir that contains your interfaces into
#  the build directory in order for your executable to find them.


from cx_Freeze import setup, Executable
from util import BOnWindows
from constants import PYSIDE, PYQT4
import qt_helper


if qt_helper.qtLib == PYSIDE:
	qtPackage = 'PySide'
	excludeQtPackage = 'PyQt4'
else:
	qtPackage = 'PyQt4'
	excludeQtPackage = 'PySide'

# Include extra modules that should be available to the interfaces.
includes = ['std_interface_imports', 'std_main_window', 'shaped_main_window', 'std_player_manager', 'std_player', 'std_progress_bar', 'img_volume_bar', 'simple_query_table', 'simple_track_query_table', 'dir_system_model']

build_exe = {'includes': includes, 'excludes': [excludeQtPackage], 'packages': [qtPackage]}

if BOnWindows():
	exe = Executable('main.py', targetName='kea.exe', base='Win32GUI', icon='kea.ico')
else:
	exe = Executable('main.py', targetName='kea')


setup(name='kea',
      version = '0.0',
      description='',
	  options = {'build_exe': build_exe},
	  executables=[exe])