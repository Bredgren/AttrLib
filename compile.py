
import re
from string import Template

label = "[a-zA-Z][a-zA-Z0-9]*"
entity_regex = re.compile("^({})\s*\{{$".format(label))
entity_end_regex = re.compile("^}$")
attribute_regex = re.compile("^   ({0}) : ({0});$".format(label))

class Attribute:
    def __init__(self, name, type, initial=None):
        self.name = name
        self.type = type
        self.initial = initial

class Entity:
    def __init__(self, name):
        self.name = name
        self.attrs = []

def parse(f):
    entities = []
    current_entity = None
    state = None
    f = open(f, 'r')
    for line in f:
        if state == None:
            m = entity_regex.match(line)
            if m:
                current_entity = Entity(m.group(1))
                state = "Entity"
        if state == "Entity":
            m = attribute_regex.match(line)
            if m:
                current_entity.attrs.append(Attribute(m.group(1), m.group(2)))
            else:
                m = entity_end_regex.match(line)
                if m:
                    entities.append(current_entity)
                    current_entity = None
                    state = None

    f.close()
    print "Entities found:"
    for entity in entities:
        print entity.name
        for attr in entity.attrs:
            print "   {} : {}".format(attr.name, attr.type)
    return entities

def writeHeader(entity):
    accessor_template = Template(
"""$type $attr(const $entity *e);
""")
    mutator_template = Template(
"""void ${attr}Is($entity *e, const $type value);
""")
    attrs = []
    funcs = ""
    for attr in entity.attrs:
        attrs.append("  {} _{};".format(attr.type, attr.name))
        funcs += accessor_template.safe_substitute({
            "entity": entity.name,
            "attr": attr.name,
            "type": attr.type
        })
        funcs += mutator_template.safe_substitute({
            "entity": entity.name,
            "attr": attr.name,
            "type": attr.type
        })

    attrs.append("  const char *_name;")
    attrs = "\n".join(attrs)

    h_out = Template(
"""#ifndef ${entupper}_H
#define ${entupper}_H

typedef struct _$entity {
$attrs
} $entity;

$entity *${entity}Init(const char *name);
void ${entity}Destroy($entity *e);
const char *name($entity *e);
$attrfuncs
#endif  // ${entupper}_H
""")
    h_out = h_out.safe_substitute({
        "entity": entity.name,
        "entupper": entity.name.upper(),
        "attrs": attrs,
        "attrfuncs": funcs
    })

    f_h = open("{}.h".format(entity.name), "w")
    f_h.write(h_out)
    f_h.close()

def writeImpl(entity):
    accessor_template = Template(
"""$type $attr(const $entity *e) {
  return e->_$attr;
}
""")
    mutator_template = Template(
"""void ${attr}Is($entity *e, const $type value) {
  if (e->_$attr == value) return;
  e->_$attr = value;
}
""")
    funcs = ""
    for attr in entity.attrs:
        funcs += accessor_template.safe_substitute({
            "entity": entity.name,
            "attr": attr.name,
            "type": attr.type
        })
        funcs += mutator_template.safe_substitute({
            "entity": entity.name,
            "attr": attr.name,
            "type": attr.type
        })

    c_out = Template(
"""
#include <stdlib.h>
#include <stdio.h>
#include "$entity.h"

$entity *${entity}Init(const char *name) {
  $entity *e = ($entity *)malloc(sizeof($entity));
  if (e != NULL) {
    e->_name = name;
  }
  return e;
}

void ${entity}Destroy($entity *e) {
  free(e);
}

const char *name($entity *e) {
  return e->_name;
}

$attrfuncs
""")
    c_out = c_out.safe_substitute({
        "entity": entity.name,
        "attrfuncs": funcs
    })

    f_c = open("{}.c".format(entity.name), "w")
    f_c.write(c_out)
    f_c.close()

def createEntity(entity):
    writeHeader(entity)
    writeImpl(entity)

def main(files):
    for f in files:
        entities = parse(f)
        for entity in entities:
            createEntity(entity)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
