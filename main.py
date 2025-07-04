#!/usr/bin/env python3
"""
Video Merger with Floating Text - GUI Application

Main entry point for the GUI application.
"""

import tkinter as tk
from tkinter import ttk
from app_gui import VideoMergerGUI
import os
os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'

# Ensure ImageMagick is in the PATH or specify its binary location
# os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
# Uncomment and set the correct path if MoviePy struggles to find ImageMagick.
# Otherwise, if ImageMagick is properly installed and in your system's PATH,
# this line might not be necessary.


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        print("Theme 'clam' not available, using default.")

    app = VideoMergerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()