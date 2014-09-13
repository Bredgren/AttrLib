
import re, os
import AttrLib.rep as rep
from setting import ATTR_LANGUAGE, LANGS_BY_EXT

class Parser(object):
    def __init__(self):
        self.atr_files = []
        self.imp_files = {}
        self.rep = None

    def find_files(self, directory):
        items = os.listdir(directory)
        for item in items:
            p = "{}/{}".format(directory, item)
            if os.path.isfile(p):
                name, ext = os.path.splitext(p)
                if ext == ATTR_LANGUAGE.extension:
                    self.atr_files.append(p)
                else:
                    if ext in LANGS_BY_EXT:
                        if ext not in self.imp_files:
                            self.imp_files[ext] = []
                        self.imp_files[ext].append(p)
            else:
                self.find_files(p)

    def parse_file(self, file_name, contents):
        line_num = 0
        mode = NamespaceMode(self.rep.global_namespace, None)
        for line in contents.split("\n"):
            line_num += 1
            if line.find("//") > -1:
                # Remove comments
                line = line[0:line.find("//")].strip()
            try:
                mode = mode.parse_line(line)
            except SyntaxError as e:
                error = e.args[0]
                error = "{}:{} {}".format(file_name, line_num, error)
                raise SyntaxError(error)

            if mode == None:
                break

    def parse_dir(self, directory):
        print "parsing", directory
        self.find_files(directory)

        print "-"*5, "Atr files:"
        for f in self.atr_files:
            print f
        print "-"*5, "Imp files:"
        for t in self.imp_files:
            print "type:", t
            for f in self.imp_files[t]:
                print "  ", f

        self.rep = rep.Rep()
        for f_name in self.atr_files:
            f = open(f_name, 'r')
            contents = f.read()
            f.close()
            self.parse_file(f_name, contents)

        return self.rep

class Mode(object):
    TAB = " " * 3
    LABEL = "[a-zA-Z_][a-zA-Z0-9_]*"
    TYPE = "(?:{label}::)*{label}".format(label=LABEL)
    VALUE = "[a-zA-Z0-9.]+"
    INT_VALUE = "[0-9]+"
    PARAM = "[a-zA-Z][a-zA-Z0-9, ]+"
    FILE = "[a-zA-Z_][a-zA-Z0-9_]*"
    ATR_FILE = "{}".format(FILE)
    IMP_FILE = "{}".format(FILE)

    def __init__(self, parent=None):
        self.parent = parent

    def parse_line(self):
        raise NotImplemented()

class NamespaceMode(Mode):
    NAMESPACE_START_RE = re.compile("^({}) : Namespace {{$".format(Mode.LABEL))
    NAMESPACE_END_RE = re.compile("^}$")
    TYPE_START_RE = re.compile(
        "^({label})\(({param})\)( : ({label}))? {{$".format(
            label=Mode.LABEL, param=Mode.PARAM))
    ENUM_START_RE = re.compile("^({}) : Enum {{$".format(Mode.LABEL))

    def __init__(self, namespace, parent):
        Mode.__init__(self, parent)
        self.namespace = namespace

    def parse_line(self, line):
        m = self.NAMESPACE_START_RE.match(line)
        if m:
            namespace_name = m.group(1)
            print "found namespace:", namespace_name
            new_namespace = rep.Namespace(namespace_name, self.namespace)
            self.namespace.namespaces[namespace_name] = new_namespace
            return NamespaceMode(new_namespace, self)

        if self.NAMESPACE_END_RE.match(line):
            return self.parent

        m = self.ENUM_START_RE.match(line)
        if m:
            enum_name = m.group(1)
            print "found enum:", enum_name
            new_enum = rep.Enum(enum_name, self.namespace)
            self.namespace.enums[enum_name] = new_enum
            return EnumMode(new_enum, self)

        m = self.TYPE_START_RE.match(line)
        if m:
            type_name = m.group(1)
            print "found type:", type_name
            params = m.group(2).split(", ")
            if m.group(4):
                super_type = self.namespace.types[m.group(4)]
            else:
                super_type = None
            new_type = rep.Type(type_name, self.namespace, params, super_type)
            self.namespace.types[type_name] = new_type
            return TypeMode(new_type, self)

        if line:
            print "Warning: Skipping unexpected line: {}".format(line)

        return self

class EnumMode(Mode):
    ENUM_END_RE = re.compile("^}$")
    ENUM_ENTRY_RE = re.compile("^{tab}({label})(?: = ({int}))?$".format(
            tab=Mode.TAB, label=Mode.LABEL, int=Mode.INT_VALUE))

    def __init__(self, enum, parent):
        Mode.__init__(self, parent)
        self.enum = enum
        self.next_value = 0

    def parse_line(self, line):
        if self.ENUM_END_RE.match(line):
            return self.parent

        if line and not line.startswith(Mode.TAB):
            raise SyntaxError("must start with 3 spaces")

        m = self.ENUM_ENTRY_RE.match(line)
        if m:
            enum_name = m.group(1)
            enum_value = self.next_value
            if m.group(2):
                enum_value = int(m.group(2))
                self.next_value = enum_value
            print "found enum value:", enum_name, enum_value
            enum_value = rep.EnumValue(enum_name, enum_value)
            self.enum.values[enum_name] = enum_value
            self.next_value += 1
            return self

        if line:
            print "Warning: Skipping unexpected line: {}".format(line)

        return self

class TypeMode(Mode):
    TYPE_END_RE = re.compile("^}$")
    ATTRIBUTE_RE = re.compile(
        "^{tab}({label}) : ({type})( = ({value}))?$".format(
            tab=Mode.TAB, label=Mode.LABEL, type=Mode.TYPE, value=Mode.VALUE))
    FUNCTION_RE = re.compile("^{tab}({label}) : ({type})\(\)$".format(
            tab=Mode.TAB, label=Mode.LABEL, type=Mode.TYPE))
    REACTOR_RE = re.compile("")

    def __init__(self, type, parent):
        Mode.__init__(self, parent)
        self.type = type

    def parse_line(self, line):
        if self.TYPE_END_RE.match(line):
            return self.parent

        if line and not line.startswith(Mode.TAB):
            raise SyntaxError("must start with 3 spaces")

        # m = self.ATTRIBUTE_RE.match(line)
        # if m:
        #     attr_name = m.group(1)
        #     attr_type = m.group(2)
        #     attr_init = m.group(4)
        #     attr = Attribute(attr_name, attr_type, attr_init)
        #     self.type.attrs.append(attr)
        #     return self

        # m = self.FUNCTION_RE.match(line)
        # if m:
        #     func_name = m.group(1)
        #     func_ret_type = m.group(2)
        #     if func_name in self.state.funcs:
        #         self.type.funcs.append(self.state.funcs[func_name])
        #     print "function: ", func_name, func_ret_type
        #     return self

        if line:
            print "Warning: Skipping unexpected line: {}".format(line)

        return self
