
class Rep(object):
    def __init__(self):
        self.types = {}
        self.funcs = {}
        # self.enums = {}

class Type(object):
    def __init__(self, name, params, super_type):
        self.name = name
        self.super_type = super_type
        self.params = params
        self.attrs = []
        self.funcs = []
        self.includes = set()

class Attribute(object):
    def __init__(self, name, type, initial=None):
        self.name = name
        self.type = type
        self.initial = initial

class Function(object):
    def __init__(self, name, decl, body):
        self.name = name
        self.decl = decl
        self.body = body
