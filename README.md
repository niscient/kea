kea
===

Open source, highly customizable music player. Currently in beta for Windows and Linux. This program allows skins (interfaces) to be made using custom Python scripts, which use the kea library and underlying PyQt or PySide framework. Two sample interfaces are supplied: Rectangular, which uses a standard Windows layout with a directory tree, a standard music track layout, and some fancy graphics, and Shaped, which looks like a desktop widget.

See the official guide for more information on using kea and creating your own interfaces: http://kea.pylonsoflight.com/guide.html

Note that kea stores the directories that make up your music library, rather than having you add the files directly. You can use the Library dialog to add new music library directories. You can also remove, rescan, or search for new files that have been created in existing music library directories. Depending on the interface, you might also have access to global hotkeys (often the number pad) that can be used to quickly restart tracks, skip to the next track, etc.

Track data is stored in a SQLite database. Music playback is currently implemented using Qt's Phonon library. The program is designed to be run either from the Python interpreter directly or from a cx_Freeze-built executable. In that case, the packaged Python interpreter will run the chosen interface, which will be supplied to the user as a raw and editable Python script. The data for each interface is stored in a separate directory, with that interface's settings (in an INI file), images, and so forth.

This project has been released under GPLv3.
