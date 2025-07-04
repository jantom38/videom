# conf.py — podstawowa konfiguracja np. dla Sphinx
import os
import sys

# Jeśli trzeba dodać ścieżkę do katalogu z plikami źródłowymi
sys.path.insert(0, os.path.abspath('.'))

# -- Ustawienia podstawowe --------------------------------------------------

project = 'NazwaTwojegoProjektu'
author = 'TwojeImię'
release = '1.0'

# -- Rozszerzenia -----------------------------------------------------------

extensions = [
    'sphinx.ext.imgconverter',  # to dodaje obsługę konwersji obrazów
]

# -- Ścieżka do ImageMagick -------------------------------------------------

# Ścieżka do pliku magick.exe
#image_converter = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
