
import re, os
from AttrLib.rep import Rep
from setting import ATTR_LANGUAGE, LANGS_BY_EXT

class Parser(object):
    def __init__(self):
        self.atr_files = []
        self.imp_files = {}

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

        return Rep()

class Mode(object):
    TAB = " " * 3
    LABEL = "[a-zA-Z_][a-zA-Z0-9_]*"
    TYPE = "{}\*?".format(LABEL)
    VALUE = "[a-zA-Z0-9.]+"
    PARAM = "[a-zA-Z][a-zA-Z0-9, ]+"
    FILE = "[a-zA-Z_][a-zA-Z0-9_]*"
    ATR_FILE = "{}.atr".format(FILE)
    IMP_FILE = "{}.c".format(FILE)

    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent

    def parse_line(self):
        raise NotImplemented()

class OuterMode(Mode):
    TYPE_START_RE = re.compile(
        "^({label})\(({param})\)( : ({label}))? {{$".format(
            label=Mode.LABEL, param=Mode.PARAM))
    INCLUDE_RE = re.compile("^include \"({})\"$".format(Mode.ATR_FILE))
    IMP_RE = re.compile("^imp \"({})\"$".format(Mode.IMP_FILE))

    def __init__(self, state):
        Mode.__init__(self, state)

    def parse_impl(self, c_file):
        c_func = re.compile(
            "(({type}\s+({label})\s*\(.*\))\s*{{[^}}]*}})".format(
                type=Mode.TYPE, label=Mode.LABEL))

        c_file = "{}/{}".format(self.state.src, c_file)
        f = open(c_file, 'r')
        contents = f.read()
        f.close()

        funcs = c_func.findall(contents)
        for func in funcs:
            name = func[2]
            decl = func[1]
            body = func[0]
            self.state.funcs[name] = Function(name, decl, body)

    def parse_line(self):
        line = self.state.line
        line_num = self.state.line_num
        types = self.state.types

        m = self.TYPE_START_RE.match(line)
        if m:
            type_name = m.group(1)
            params = m.group(2).split(", ")
            if m.group(4):
                super_type = types[m.group(4)]
            else:
                super_type = None
            return TypeMode(self.state, self, type_name, params, super_type)

        m = self.INCLUDE_RE.match(line)
        if m:
            print "include", m.group(1)
            return self

        m = self.IMP_RE.match(line)
        if m:
            print "imp", m.group(1)
            self.parse_impl(m.group(1))
            return self

        if line != '\n':
            print "Unexpected line: {} - {}".format(line_num, line.strip())

        return self

class TypeMode(Mode):
    TYPE_END_RE = re.compile("^}$")
    ATTRIBUTE_RE = re.compile(
        "^{tab}({label}) : ({type})( = ({value}))?$".format(
            tab=Mode.TAB, label=Mode.LABEL, type=Mode.TYPE, value=Mode.VALUE))
    FUNCTION_RE = re.compile("^{tab}({label}) : ({type})\(\)$".format(
            tab=Mode.TAB, label=Mode.LABEL, type=Mode.TYPE))
    REACTOR_RE = re.compile("")

    def __init__(self, state, parent, type_name, type_params, super_type):
        Mode.__init__(self, state, parent)
        self.type = Type(type_name, type_params, super_type)

    def parse_line(self):
        line = self.state.line
        line_num = self.state.line_num
        types = self.state.types

        if self.TYPE_END_RE.match(line):
            return self.parent

        if not line.startswith(Mode.TAB):
            raise SyntaxError(
                "Line: {} - must start with 3 spaces".format(line_num))

        m = self.ATTRIBUTE_RE.match(line)
        if m:
            attr_name = m.group(1)
            attr_type = m.group(2)
            attr_init = m.group(4)
            attr = Attribute(attr_name, attr_type, attr_init)
            self.type.attrs.append(attr)
            return self

        m = self.FUNCTION_RE.match(line)
        if m:
            func_name = m.group(1)
            func_ret_type = m.group(2)
            if func_name in self.state.funcs:
                self.type.funcs.append(self.state.funcs[func_name])
            print "function: ", func_name, func_ret_type
            return self

        if line != '\n':
            print "Unexpected line: {} - {}".format(line_num, line.strip())

        return self
