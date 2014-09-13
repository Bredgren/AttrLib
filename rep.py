
# TODO:
#    Built-in Types:
#       U64, U32, U8
#       S64, S32, S8
#       Float, Double
#       String
#       Char

class Rep(object):
    def __init__(self):
        self.global_namespace = Namespace("")

class ImpFile(object):
    def __init__(self, name):
        self.name = name

class Type(object):
    def __init__(self, name, parent, type_params, super_type=None):
        self.name = name
        self.parent = parent
        self.super_type = super_type
        self.params = type_params
        self.attrs = []
        self.funcs = []
        self.reacs = []
        self.imp_files = []

class TypeParam(object):
    def __init__(self, param_name):
        self.name = param_name

class Attribute(object):
    def __init__(self, name, parent, value_type, key_type=None, initial=None):
        self.name = name
        self.parent = parent
        self.key_type = key_type
        self.value_type = value_type
        self.initial = initial

class Function(object):
    def __init__(self, name, parent, return_type, func_params):
        self.name = name
        self.parent = parent
        self.return_type = return_type
        self.params = func_params

class FuncParam(object):
    def __init__(self, param_type):
        self.type = param_type

class Reaction(object):
    def __init__(self, parent, attr_owner, attr, handle_func):
        self.parent = parent
        self.attr_owner = attr_owner
        self.attr = attr
        self.handle_func = handle_func

class EnumValue(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Enum(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.values = {}

class Namespace(object):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.namespaces = {}
        self.types = {'Entity': None}
        self.enums = {}
