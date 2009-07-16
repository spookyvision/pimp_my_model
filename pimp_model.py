#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# Anatol Ulrich, au@hypnocode.net
#
# Xcode user script to automatically add properties and an initializer to an ObjC model class
#
# License: GPLv2
#
# TODO: this really needs a proper ObjC parser, nudging regexps is no fun
# TODO: I'm using separate slots for every Mutator, probably unnecessary complexity
# TODO: maybe add comments as markers for ivars to tell generator what to leave out, override "retain" etc
# TODO: remove some superfluous newlines

import sys
import string
import re

class Argument(object):
    def __init__(self, ctype, name):
        self.ctype = ctype
        self.name = name
    @property
    def inName(self):
        return "in" + self.camelName
    @property
    def camelName(self):
        return self.name[0].capitalize() + self.name[1:]
    def signaturePart(self, first = False):
        if first:
            selectorFragment = "initWith" + self.camelName + ":"
        else:
            selectorFragment = self.name + ":"
        return "%s (%s) %s" % (selectorFragment, self.ctype, self.inName)
    def __unicode__(self):
        return "<Argument: %s %s>" % (self.ctype, self.name)


class HeaderImplPair(object):
    def __init__(self, header, impl):
        self.header = header
        self.impl = impl
    def addImplHook(self, hook, context_regex, before=True, newline = True):
        self.impl = self.addHook(hook, self.impl, context_regex, before, newline)
    def addHeaderHook(self, hook, context_regex, before=True, newline = True):
        self.header = self.addHook(hook, self.header, context_regex, before, newline)
    def addHook(self, hook, string, context_regex, before, with_newline = True):
        grouped_regex = "(" + context_regex + ")"
        if with_newline:
            hook = '\n' + hook + '\n'
        if before:
            replace_string = hook + r'\1'
        else:
            replace_string = r'\1' + hook
        return re.sub(grouped_regex, replace_string, string)


class Mutator(object):
    def __init__(self, headerAndImpl, hook=None, headerHookRegex = "", implHookRegex = None, before_header = True, before_impl = True):
        self.items = []
        self.itemNames = {}
        self.hook = hook
        self.headerAndImpl = headerAndImpl
        self.before_header = before_header
        self.before_impl = before_impl
        if implHookRegex is None:
            implHookRegex = headerHookRegex
        self.implHookRegex = implHookRegex
        self.headerHookRegex = headerHookRegex
        self.header_newline = True
        self.impl_newline = True
    def add(self, item, name=None):
        """maybe we'll need this one day. It's for containers!"""
        if name:
            self.itemNames[name] = item
            self.items.append(item)
    def extendHook(self, template, replacement):
        return template.replace(self.hook, replacement)
    @property
    def headerPart(self):
        return ""
    @property
    def implPart(self):
        return ""
    def renderImpl(self, impl):
        return self.extendHook(impl, self.implPart)
    def renderHeader(self, header):
        return self.extendHook(header, self.headerPart)
    def addHooks(self):
        if self.headerHookRegex:
            self.headerAndImpl.addHeaderHook(self.hook, self.headerHookRegex, self.before_header, self.header_newline)
        if self.implHookRegex:
            self.headerAndImpl.addImplHook(self.hook, self.implHookRegex, self.before_impl, self.impl_newline)
    def render(self):
        # TODO addHooks() should be separate (otherwise the hook string can always be the same --> go that route? Separate hook strings are nice in theory, but when do we need them?)
        self.addHooks()
        self.headerAndImpl.header = self.renderHeader(self.headerAndImpl.header)
        self.headerAndImpl.impl = self.renderImpl(self.headerAndImpl.impl)
    def __unicode__(self):
        template = """<%s>
======= header part: =======
%s

======== impl part: ========
%s
"""
        return template % (self.__class__.__name__, self.headerPart, self.implPart)


class Constructor(Mutator):
    template = """
%(signature)s {
    
    if (self = [super init]) {
%(assignments)s
    }
    
    return self;
}
    """
    def __init__(self, headerImpl, args):
        Mutator.__init__(self, headerImpl, '$constructor$', '@end')
        self.args = args
        self.signature = self.makeSignature()
    def makeSignature(self):
        signature = "-(id) "
        first = True
        for arg in self.args:
            signature += arg.signaturePart(first) + " "
            first = False
        return signature.rstrip()
    def makeAssignments(self):
        result = ""
        indent = "             "
        for arg in self.args:
            result += "%sself.%s = %s;\n" % (indent, arg.name, arg.inName)
        return result
    @property
    def headerPart(self):
        return self.signature + ";"
    @property
    def implPart(self):
        return Constructor.template % dict(
                signature = self.signature,
                assignments = self.makeAssignments()
                )


class Synthesize(Mutator):
    def __init__(self, headerImpl):
        Mutator.__init__(self, headerImpl, '$synthesize$', '', '@implementation.*', False, False)
    @property
    def implPart(self):
        return '@synthesize ;'

class Property(Mutator):
    def __init__(self, headerImpl, arg, behavior, default_behavior = ['nonatomic'], is_last = False):
        Mutator.__init__(self, headerImpl, '$properties$', '@end', '@synthesize ', True, False)
        behavior.extend(default_behavior)
        self.behavior = behavior
        self.arg = arg
        self.is_last = is_last
        self.header_newline = True
        self.impl_newline = False
    @property
    def implPart(self):
        result = self.arg.name
        if not self.is_last:
            result += ", "
        return result
    @property
    def headerPart(self):
        arg = self.arg
        return "@property(%s) %s %s;" % (
                ','.join(self.behavior),
                arg.ctype,
                arg.name
                )

class Dealloc(Mutator):
    def __init__(self, headerImpl):
        Mutator.__init__(self, headerImpl, '$dealloc$', '', '@end')
    @property
    def implPart(self):
        return """-(void) dealloc {
    [super dealloc];
}
"""

class Release(Mutator):
    def __init__(self, headerImpl, ivar):
        Mutator.__init__(self, headerImpl, '$release$', '', '.*\[super dealloc\]')
        self.ivar = ivar
    @property
    def implPart(self):
        return "    [%s release];" % self.ivar

def read(filename):
    fh = open(filename,"r")
    result = fh.read()
    fh.close()
    return result

def main():
    run("""%%%{PBXFilePath}%%%""")

def run(header):
    implementation = header[:-2] + ".m"

    header_content = read(header)
    implementation_content = read(implementation)

    header_content = header_content.replace('}\n', '}\n')

    hi = HeaderImplPair(header_content, implementation_content)
    Dealloc(hi).render()

    ivars = re.search(r'^.*{(.*)}.*$', header_content, re.DOTALL).groups()[0].split(';')
    properties = []
    args = []
    for ivar in ivars:
        ivar = ivar.strip()
        if not ivar: continue
        ivar = re.sub(';$','', ivar)
        ctype, name = re.sub(" +", " ", re.sub(r'\**', '', ivar)).split(" ",1)
        is_reference = "*" in ivar
        if is_reference:
            # it's a pointer -> retain property
            behavior = ["retain"]
            ctype += "*"
            Release(hi, name).render()
        else:
            # assume assign
            behavior = ["assign"]
        arg = Argument(ctype, name)
        args.append(arg)
        properties.append(Property(hi, arg, behavior))
    properties.reverse()
    properties[0].is_last = True
    synthesize = Synthesize(hi)
    synthesize.render()
    for property in properties:
        property.render()
    c = Constructor(hi, args)
    c.render()
    debug = False
    if debug:
        print header
        print hi.header
        print "====="
        print hi.impl
    def overwrite(fn, newstr):
        fh = open(fn,"w")
        fh.write(newstr)
        fh.close()
    do_overwrite = True
    if do_overwrite:
        overwrite(header, hi.header)
        overwrite(implementation, hi.impl)
    #new_header = open(header, 'w')
    #new_header.write(hi.header)
    #new_header.close()

    #new_impl = open(implementation, 'w')
    #new_impl.write(hi.impl)
    #new_impl.close()

if __name__=="__main__": main()
