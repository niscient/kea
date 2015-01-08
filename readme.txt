   kea v1.0

 Created by Rains Jordan

   >>  kea.pylonsoflight.com  <<


kea is an open-source, cross-platform, highly customizable music player which uses Python and Qt.




===================
=-- Basic Usage --=


You can use kea to play music files located on your computer.

kea stores the directories that make up your music library, rather than having you add the files directly. You can use the Library dialog to add new music library directories. You can also remove, rescan, or search for new files that have been created in existing music library directories.

Keyboard shortuts and so on vary by interface. You can navigate the interface using the arrow keys, Enter, etc, and play/pause the current track with Space. There are also several global hotkeys, which work regardless of whether the program window is active or minimized:

Keypad 4: Previous track
Keypad 6: Previous track
Keypad 5: Play random track from current playlist
Keypad 8: Play/pause current track
Keypad 2: Restart track

Ctrl+Left, Ctrl+Right, Ctrl+Down, Ctrl+Up, and Ctrl+Alt+Left are the usual non-global clones of these hotkeys. Ctrl+Alt+Up and Ctrl+Alt+Down fiddle with the volume. Ctrl+Q quits the program. Ctrl+T usually selects a tree, Ctrl+R usually selects a table/playlist, and Ctrl+F usually opens a search feature. Alt+Left and Alt+Right might navigate between window panes, if they exist. Depending on the platform, Home or Ctrl+Home and the End equivalent may be used for navigating a table.

Currently, the only way to implement album art is to put a PNG or JPG file named folder or album into the album directory.


====================
=-- Installation --=

You can run kea as a stand-alone executable, or you can run the source code from the Python interpreter. (The main file is 'main.py'.) Currently, only Python 2 is supported, due to mutagen's current lack of support for Python 3 and hsaudiotag3k 1.1.3's problems loading ID3v2.4 tags.

Running kea from the source code allows you to create (and, if you want, release) your own custom interfaces. To do this, you'll have to install a few external libraries:

PySide or PyQt4 (only PyQt4 supports global hotkeys)
mutagen
PyGlobalShortcut (optional; for mapping global hotkeys)
cx_Freeze (if you want to create your own executables)

(PyGlobalShortcut is based on libqxt's QxtGlobalShortcut, which has problems with certain key combinations. So I've also included a custom Win32 global hotkey-mapping system which uses the native ctypes module.)


=========================
=-- Custom Interfaces --=

The existing interfaces for kea are extensions of the Qt framework. You can create custom interfaces using a combination of Python and Qt by creating new folders and .py files inside the interfaces folder. These interfaces can extend the capability of the existing interfaces or use any other Qt (or other library) features.

Components within existing interfaces are generally encapsulated into separate .py files. Feel free to reuse any code from the existing interfaces. Add an interface's name to the [Interfaces] section of kea.ini to allow transitions to that interface from existing interfaces.

Each interface should be created as a named directory inside the 'interfaces' directory. Inside the named directory should be a .py file of the same name, which will be treated as that interface's main program file, and an .ini file of the same name, which will be used to store that interface's configuration data. There will also be another .ini file, of the same name as the main .ini file but followed by the string '_reset'. Since user-activated changes to the way an interface works are stored in the main interface, any attempt to reset the interface to its default state will overwrite the main .ini file with this reset file.

Additionally, on Python 2 (currently the only supported version of Python), empty files named __init__.py must be placed in the 'interfaces' directory, as well as each of the actual directories used by the interfaces.


=========================
=-- Building kea --=

You can create and release custom interface packages by themselves, and other users can use them, as long as they're compatible with the standard kea distribution. However, you might want to modify and release changes to the code for kea's main engine itself.

You're welcome to package and distribute your own executables as long as your program states that it's using the kea engine, and you release your source code. (See the GPLv3 license.) To build an executable, install and use the cx_Freeze library. kea comes with a setup.py file, on which you should run 'python setup.py build' (assuming that Python 2 is your default version of Python).

Windows only: When running the built executable, you will have problems with Qt not being able to find its SQL drivers. To fix this, copy the sqldrivers directory from your Python installation's site-packages/PySide/plugins directory (or the PyQt4 equivalent) into the directory that contains your built executable. (To be exact, the only DLL you need from the sqldrivers dir is qsqlite4.)

You will also need to put kea.ini and the 'interfaces' dir that contains your interfaces into the build directory in order for your executable to find them.


===================
=-- Information --=


kea is released under the GPLv3 license.


Libraries used      Authors
 PySide              Qt Project
 PyQt4               Riverbank Computing
 mutagen             Christoph Reiter
 PyGlobalShortcut    J. Matt Peterson, Asvel
 cx_Freeze           Anthony Tuininga, Computronix



Copyright © 2014 Rains Jordan