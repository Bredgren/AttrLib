
class File(object):
    def __init__(self, name, contents):
        self.name = name
        self.contents = contents

class Writer(object):
    def __init__(self):
        self.files = []

    def construct(self, rep):
        pass

    def write(self, out_dir):
        pass
