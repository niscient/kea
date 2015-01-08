# Various constants


PYSIDE, PYQT4 = 0, 1

UNSORTED, SORTED_ASC, SORTED_DESC = 0, 1, 2

# Tuple positions for tag data.
DB_TITLE, DB_ARTIST_ID, DB_ALBUM_ID, DB_TRACK, DB_LENGTH, DB_YEAR, DB_GENRE_ID, DB_PATH = 0, 1, 2, 3, 4, 5, 6, 7

# These positions are the same regardless of whether we're dealing with the string or the ID.
DB_ARTIST = DB_ARTIST_ID
DB_ALBUM = DB_ALBUM_ID
DB_GENRE = DB_GENRE_ID

FAILURE, SUCCESS, PARTIAL_SUCCESS = 0, 1, 2

# Win32 constants
VK_NUMPAD1, VK_NUMPAD2, VK_NUMPAD3, VK_NUMPAD4, VK_NUMPAD5, VK_NUMPAD6, VK_NUMPAD7, VK_NUMPAD8, VK_NUMPAD9 = range(97, 106)
WM_HOTKEY = 786