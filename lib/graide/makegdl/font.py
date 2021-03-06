#    Copyright 2012, SIL International
#    All rights reserved.
#
#    This library is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation; either version 2.1 of License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should also have received a copy of the GNU Lesser General Public
#    License along with this library in the file named "LICENSE".
#    If not, write to the Free Software Foundation, 51 Franklin Street,
#    suite 500, Boston, MA 02110-1335, USA or visit their web page on the 
#    internet at http://www.fsf.org/licenses/lgpl.html.

import os, re, traceback
from graide.makegdl.glyph import Glyph
from graide.makegdl.psnames import Name
from xml.etree.cElementTree import ElementTree, parse, Element

# A collection of glyphs that have a given attachment point defined
class PointClass(object) :

    def __init__(self, name) :
        self.name = name
        self.glyphs = []
        self.dias = []
#        self.isBase = False

    def addBaseGlyph(self, g) :
        self.glyphs.append(g)
#        if g.isBase : self.isBase = True

    def addDiaGlyph(self, g) :
        self.dias.append(g)

    def hasDias(self) :
        if len(self.dias) and len(self.glyphs) :
            return True
        else :
            return False

    def classGlyphs(self, isDia = False) :
        if isDia :
            return self.dias
        else :
            return self.glyphs

    def isNotInClass(self, g, maxGid, isDia = False) :
        if not g : return False
        # Don't include pseudo-glyphs:
        if g.gid > maxGid : return False
            
        if isDia :
            return g not in self.dias
        else :
            return g not in self.dias and g not in self.glyphs


class FontClass(object) :

    def __init__(self, elements = None, fname = None, lineno = None, generated = False, editable = False) :
        self.elements = elements or []
        self.fname = fname
        self.lineno = lineno
        self.generated = generated
        self.editable = editable

    def append(self, element) :
        self.elements.append(element)


class Font(object) :
    
    def __init__(self) :
        self.glyphs = []
        self.psnames = {}
        self.canons = {}
        self.gdls = {}
        self.anchors = {}
        self.ligs = {}
        self.subclasses = {}
        self.points = {}
        self.classes = {}

    def __len__(self) :
        return len(self.glyphs)

    # [] syntax returns the indicated element of the glyphs array.
    def __getitem__(self, y) :
        try :
            return self.glyphs[y]
        except IndexError :
            return None

    def emunits(self) :
        return 0

    def initGlyphs(self, nGlyphs) :
        #print "Font::initGlyphs",nGlyphs
        self.glyphs = [None] * nGlyphs
        self.numRealGlyphs = nGlyphs  # does not include pseudo-glyphs
        self.psnames = {}
        self.canons = {}
        self.gdls = {}
        self.classes = {}

    def addGlyph(self, index = None, psName = None, gdlName = None, factory = Glyph) :
        #print "Font::addGlyph",index,psName,gdlName
        g = factory(psName, index) # create a new glyph of the given class
        self.renameGlyph(g, g.psname, gdlName)
        if index is None :  # give it the next available index
            index = len(self.glyphs) 
            self.glyphs.append(g)
        elif index >= len(self.glyphs) :
            self.glyphs.extend([None] * (len(self.glyphs) - index + 1))
        self.glyphs[index] = g
        return g

    def addGdxGlyph(self, e, apFileName) :
        hasApFile = not not apFileName  # if there is an AP XML File, very little gets set here
                                        # (most of the glyph attrs get set directly from the XML file),
                                        # but we do need to set actualForPseudo, and also the glyph name
        gid = int(e.get('glyphid'))
        
        g = self[gid]
        gdlName = e.get('className')    # single-value "class", eg 'g_dollar'
        if gdlName and re.match('^\*GC\d+\*$', gdlName) :  # autogenerated pseudo-glyph
            gdlName = None
        if not g :
            if gid > len(self.glyphItems) :
                canonName = Name.createFromGDL(gdlName).canonical() if gdlName else None  # postscript-style name
                if canonName :
                    g = self.addGlyph(gid, canonName, None)
                else :
                    g = self.addGlyph(gid, canonName, gdlName)
            else :
                g = self.addGlyph(gid)

        if not hasApFile :
            g.clear()
        if gdlName : self.setGDL(g, gdlName)
        storemirror = False
        u = e.get('usv')
        if u and u.startswith('U+') : u = u[2:]
        if u : g.uid = u
            
        inFile = e.get("inFile")
        atLine = e.get("atLine")
        atLine = int(atLine)-1 if atLine else -1  # subtract 1 because GDX is 1-based but file editor is 0-based
        if inFile : g.addLineAndFile("gid", inFile, atLine)
            
        for a in e.iterfind('glyphAttrValue') :
            attrName = a.get('name')
            
            inFile = a.get("inFile")
            atLine = a.get("atLine")
                
            m = re.match(ur'^justify.(\d).([^.]+)', attrName)
            if m :
                g.setjustify(int(m.group(1)), m.group(2), a.get('value'))
            elif attrName == 'mirror.isEncoded' :
                storemirror = True
            elif attrName == 'mirror.glyph' :
                mirrorglyph = a.get('value')
            elif attrName.startswith('collision') :
                g.setCollisionProp(attrName[10:], int(a.get('value')))
            elif attrName.startswith('sequence') :
                g.setSequenceProp(attrName[9:], int(a.get('value')))
            elif attrName.startswith('octabox') :
                g.setOctaboxProp(attrName[8:], a.get('value'))
            elif g.builtInGlyphAttr(attrName) :
                g.setGdlProperty(attrName, a.get('value'))
            #elif hasApFile :
            #    pass 
            # AP file takes precedent for AP attributes so skip them
            elif attrName.endswith('.x') and not hasApFile : 
                g.setAnchor(attrName[:-2], int(a.get('value')), None)
            elif attrName.endswith('.y') and not hasApFile :
                g.setAnchor(attrName[:-2], None, int(a.get('value')))
            else :
                g.setUserProperty(attrName, a.get('value'))
            
            if inFile :
                atLine = int(atLine) - 1 if atLine else -1
                g.addLineAndFile(attrName, inFile, atLine)

        if storemirror and mirrorglyph :
            g.setGdlProperty('mirror.glyph', mirrorglyph)
            g.setGdlProperty('mirror.isEncoded', '1')
            

    def renameGlyph(self, g, name, gdlName = None) :
        if g.psname != name :
            for n in g.parseNames() :
                del self.psnames[n.psname]
                del self.canons[n.canonical()]
        if gdlName :
            self.setGDL(g, gdlName)
        else :
            self.setGDL(g, g.GDLName())
        for n in g.parseNames() :
            if n is None : break
            self.psnames[n.psname] = g
            self.canons[n.canonical()] = (n, g)

    def setGDL(self, glyph, name) :
        if not glyph : return
        n = glyph.GDLName()
        if n != name and n in self.gdls : del self.gdls[n]
        if name and name in self.gdls and self.gdls[name] is not glyph :
            count = 1
            index = -2
            name = name + "_1"
            while name in self.gdls :
                if self.gdls[name] is glyph : break
                count = count + 1
                name = name[0:index] + "_" + str(count)
                if count == 10 : index = -3
                if count == 100 : index = -4
        self.gdls[name] = glyph
        glyph.setGDL(name)

    def addClass(self, name, elements, fname = None, lineno = 0, generated = False, editable = False) :
        self.classes[name] = FontClass(elements, fname, lineno, generated, editable)
        for e in elements :
            g = self[e]
            if g : g.addClass(name)

    def addGlyphClass(self, name, gid, editable = False) :
        if name not in self.classes :
            self.classes[name] = FontClass()
        if gid not in self.classes[name].elements :
            self.classes[name].append(gid)

    def classUpdated(self, name, value) :
        c = []
        if name in self.classes :
            for gid in self.classes[name].elements :
                g = self[gid]
                if g : g.removeClass(name)
        if value is None and name in classes :
            del self.classes[name]
            return
        for n in value.split() :
            g = self.gdls.get(n, None)
            if g :
                c.append(g.gid)
                g.addClass(name)
        if name in self.classes :
            self.classes[name].elements = c
        else :
            self.classes[name] = FontClass(c)

    # Return the list of classes that should be updated in the AP XML file.
    # This does not include classes that are auto-generated or defined in the hand-crafted GDL code.
    def filterAutoClasses(self, names, autoGdlFile) :
        res = []
        for n in names :
            c = self.classes[n]
            if not c.generated and (not c.fname or c.fname == autoGdlFile) : res.append(n)
        return res

    # TODO: move this method to GraideFont, or refactor
    def loadAP(self, apFileName) :
        if not os.path.exists(apFileName) : return False
        self.initGlyphs() # ??? how many glyphs are there?
        etree = parse(apFileName)
        i = 0
        for e in etree.getroot().iterfind("glyph") :
            g = self.addGlyph(i, e.get('PSName'))
            g.readAP(e, self)
            i += 1
        return True

    def saveAP(self, apFileName, autoGdlFile) :
        root = Element('font')
        root.set('upem', str(self.emunits()))
        root.set('producer', 'graide 1.0')
        root.text = "\n\n"
        for g in self.glyphs :
            if g : g.createAP(root, self, autoGdlFile)
        ElementTree(root).write(apFileName, encoding="utf-8", xml_declaration=True)

    def createClasses(self) :
        self.subclasses = {}
        for k, v in self.canons.items() :
            if v[0].ext :
                h = v[0].head()
                o = self.canons.get(h.canonical(), None)
                if o :
                    if v[0].ext not in self.subclasses : self.subclasses[v[0].ext] = {}
                    self.subclasses[v[0].ext][o[1].GDLName()] = v[1].GDLName()
#        for g in self.glyphs :
#            if not g : continue
#            for c in g.classes :
#                if c not in self.classes :
#                    self.classes[c] = []
#                self.classes[c].append(g.gid)

    def calculatePointClasses(self) :
        self.points = {}
        for g in self.glyphs :
            if not g : continue
            for apName in g.anchors.keys() :
                genericName = apName[:-1] # without the M or S
                if genericName not in self.points :
                    self.points[genericName] = PointClass(genericName)
                if apName.endswith('S') : 
                    self.points[genericName].addBaseGlyph(g)
                else :
                    self.points[genericName].addDiaGlyph(g)
    
    def getPointClasses(self) :
        if len(self.points) == 0 :
            self.calculatePointClasses()
        return self.points

    def ligClasses(self) :
        self.ligs = {}
        for g in self.glyphs :
            if not g or not g.name : continue
            (h, t) = g.name.split_last()
            if t :
                o = self.canons.get(h.canonical(), None)
                if o and o[0].ext == t.ext :
                    t.ext = None
                    t.cname = None
                    tn = t.canonical(noprefix = True)
                    if tn in self.ligs :
                        self.ligs[tn].append((g.GDLName(), o[0].GDL()))
                    else :
                        self.ligs[tn] = [(g.GDLName(), o[0].GDL())]

    def outGDL(self, fh) :
        munits = self.emunits()
        fh.write('table(glyph) {MUnits = ' + str(munits) + '};\n')
        nglyphs = 0
        for g in self.glyphs :
            if not g or not g.psname : continue
            if g.psname == '.notdef' :
                fh.write(g.GDLName() + ' = glyphid(0)')
            else :
                fh.write(g.GDLName() + ' = postscript("' + g.psname + '")')
            outs = []
            if len(g.anchors) :
                for a in g.anchors.keys() :
                    v = g.anchors[a]
                    outs.append(a + "=point(" + str(int(v[0])) + "m, " + str(int(v[1])) + "m)")
            for (p, v) in g.gdlProperties.items() :
                if p == "*skipPasses*" :
                    pass  # ignore this one
                else :
                    outs.append("%s=%s" % (p, v))
            if len(outs) : fh.write(" {" + "; ".join(outs) + "}")
            fh.write(";\n")
            nglyphs += 1
        fh.write("\n")
        fh.write("\n/* Point Classes */\n")
        for p in self.points.values() :
            if not p.hasDias() : continue
            n = p.name + "Dia"
            self.outclass(fh, "c" + n, p.classGlyphs(True))
            self.outclass(fh, "cTakes" + n, p.classGlyphs(False))
            self.outclass(fh, 'cn' + n, filter(lambda x : p.isNotInClass(x, self.numRealGlyphs, True), self.glyphs))
            self.outclass(fh, 'cnTakes' + n, filter(lambda x : p.isNotInClass(x, self.numRealGlyphs, False), self.glyphs))
        fh.write("\n/* Classes */\n")
        for (c, l) in self.classes.items() : # c = class name, l = class object
            if c not in self.subclasses and not l.generated :  # don't output the class to the AP file if it was autogenerated
                self.outclass(fh, c, map(lambda x: self.glyphs[x], l.elements))
        for p in self.subclasses.keys() :
            ins = []
            outs = []
            for k, v in self.subclasses[p].items() :
                ins.append(k)
                outs.append(v)
            n = p.replace('.', '_')
            self.outclass(fh, 'cno_' + n, ins)
            self.outclass(fh, 'c' + n, outs)
        fh.write("/* Ligature Classes */\n")
        for k in self.ligs.keys() :
            self.outclass(fh, "clig" + k, map(lambda x: self.gdls[x[0]], self.ligs[k]))
            self.outclass(fh, "cligno_" + k, map(lambda x: self.gdls[x[1]], self.ligs[k]))
        fh.write("\nendtable;\n")
        fh.write("\n\n#define MAXGLYPH %d\n\n" % (nglyphs - 1))

    def outPosRules(self, fh, num) :
        fh.write("""
#ifndef opt2
#define opt(x) [x]?
#define opt2(x) [opt(x) x]?
#define opt3(x) [opt2(x) x]?
#define opt4(x) [opt3(x) x]?
#endif
#define posrule(x) cTakes##x##Dia c##x##Dia {attach {to=@1; at = x##S; with = x##M}; user1=1} \\
                        / ^ _ opt4(cnTakes##x##Dia) _{user1==0}

table(positioning);
pass(%d);
""" % num)
        for p in self.points.values() :
            if p.hasDias() :
                fh.write("posrule(%s);\n" % p.name)
        fh.write("endpass;\nendtable;\n")


    def outclass(self, fh, name, glyphs) :
        fh.write(name + " = (")
        count = 1
        sep = ""
        for g in glyphs :
            if not g : continue
                
                
            if isinstance(g, basestring) :
                fh.write(sep + g)
            else :
                if g.GDLName() is None :
                    print "Can't output " + str(g.gid) + " to class " + name
                else :
                    fh.write(sep + g.GDLName())
            if count % 8 == 0 :
                sep = ',\n         '
            else :
                sep = ', '
            count += 1
        fh.write(');\n\n')

