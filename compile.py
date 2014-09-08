
import re
from string import Template

class State:
    def __init__(self):
        self.types = {}
        self.funcs = {}
        self.line_num = 0
        self.line = ""
        self.modes = []
        self.mode = None
        self.src = ""

class Mode:
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

class Type:
    def __init__(self, name, params, super_type):
        self.name = name
        self.super = super_type
        self.params = params
        self.attrs = []
        self.funcs = []
        self.includes = set()

class Attribute:
    def __init__(self, name, type, initial=None):
        self.name = name
        self.type = type
        self.initial = initial

class Function:
    def __init__(self, name, decl, body):
        self.name = name
        self.decl = decl
        self.body = body

def parse(src, f):
    state = State()
    state.src = src
    state.mode = OuterMode(state)
    f = open(f, 'r')
    for line in f:
        state.line = line
        state.line_num += 1
        new_mode = state.mode.parse_line()
        if new_mode != state.mode:
            if isinstance(state.mode, TypeMode):
                state.types[state.mode.type.name] = state.mode.type
            state.mode = new_mode

    f.close()
    print "Types found:"
    for t in state.types.values():
        print "{} - {}".format(t.name, t.params)
        if t.super:
            print "   super ->", t.super.name
        for attr in t.attrs:
            print "   {} : {}".format(attr.name, attr.type)

    return state.types.values()

def writeHeader(dest, type):
    accessor_template = Template(
"""$type ${type}_$attr(const $type* e);
""")
    mutator_template = Template(
"""void ${type}_${attr}Is($type* e, const $attr_type value);
""")
    attrs = []
    funcs = ""
    for attr in type.attrs:
        attrs.append("  {} _{};".format(attr.type, attr.name))
        funcs += accessor_template.safe_substitute({
            "type": type.name,
            "attr": attr.name,
            "attr_type": attr.type
        })
        funcs += mutator_template.safe_substitute({
            "type": type.name,
            "attr": attr.name,
            "attr_type": attr.type
        })

    attrs = "\n".join(attrs)

    h_out = Template(
"""#ifndef ${typeupper}_H
#define ${typeupper}_H

typedef struct _$type {
$attrs
} $type;

$type* ${type}_init(const char* name);
void ${type}_destroy($type* e);
const char* ${type}_name($type* e);
$attrfuncs
#endif  // ${typeupper}_H
""")
    h_out = h_out.safe_substitute({
        "type": type.name,
        "typeupper": type.name.upper(),
        "attrs": attrs,
        "attrfuncs": funcs
    })

    f_h = open("{}/{}.h".format(dest, type.name), "w")
    f_h.write(h_out)
    f_h.close()

def writeImpl(dest, type):
    accessor_template = Template(
"""$attr_type ${type}_$attr(const $type* e) {
  return e->_$attr;
}
""")
    mutator_template = Template(
"""void ${type}_${attr}Is($type* e, const $attr_type value) {
  if (e->_$attr == value) return;
  e->_$attr = value;
}
""")
    funcs = ""
    attr_init = []
    for attr in type.attrs:
        if attr.initial:
            attr_init.append("    e->_{} = {};".format(attr.name, attr.initial))
        funcs += accessor_template.safe_substitute({
            "type": type.name,
            "attr": attr.name,
            "attr_type": attr.type
        })
        funcs += mutator_template.safe_substitute({
            "type": type.name,
            "attr": attr.name,
            "attr_type": attr.type
        })

    attr_init = "\n".join(attr_init)

    c_out = Template(
"""
#include <stdlib.h>
#include <stdio.h>
#include "$type.h"

$type* ${type}_init(const char* name) {
  $type *e = ($type*)malloc(sizeof($type));
  if (e != NULL) {
    e->_name = name;
$attr_init
  }
  return e;
}

void ${type}_destroy($type* e) {
  free(e);
}

const char* ${type}_name($type* e) {
  return e->_name;
}

$attrfuncs
""")
    c_out = c_out.safe_substitute({
        "type": type.name,
        "attr_init": attr_init,
        "attrfuncs": funcs
    })

    f_c = open("{}/{}.c".format(dest, type.name), "w")
    f_c.write(c_out)
    f_c.close()

def createType(dest, type):
    writeHeader(dest, type)
    writeImpl(dest, type)

def main(src, dest, files):
    for f in files:
        types = parse(src, f)
        for t in types:
            createType(dest, t)

if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
