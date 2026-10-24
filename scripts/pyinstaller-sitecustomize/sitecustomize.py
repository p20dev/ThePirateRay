"""Keep PyInstaller's isolated analysis from initializing a GTK display."""

import gi


gi.disable_legacy_autoinit()
