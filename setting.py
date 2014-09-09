
from AttrLib.c_writer import CWriter

class Language(object):
    def __init__(self, name, writer, extension):
        self.name = name
        self.writer = writer
        self.extension = extension

ATTR_LANGUAGE = Language("Attr", None, ".atr")

LANGUAGES = [
    Language("C", CWriter, ".c")
    # "Python": PythonWriter
]

LANGS_BY_NAME = {l.name: l for l in LANGUAGES}
LANGS_BY_EXT = {l.extension: l for l in LANGUAGES}
