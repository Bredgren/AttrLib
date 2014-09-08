
from AttrLib.writer import Writer

class CWriter(Writer):
    def __init__(self):
        Writer.__init__(self)

    def construct(self, rep):
        print "constructing from", rep

    def write(self, out_dir):
        print "writing to", out_dir
        
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
