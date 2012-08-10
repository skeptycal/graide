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


from PySide import QtGui
from graide import freetype
import array, ctypes
from graide.attribview import Attribute, AttribModel
from graide.utils import DataObj
from graide.makegdl.glyph import Glyph as gdlGlyph

def ftGlyph(face, gid) :
    res = freetype.FT_Load_Glyph(face._FT_Face, gid, freetype.FT_LOAD_RENDER)
    b = face.glyph.bitmap
    top = face.glyph.bitmap_top
    left = face.glyph.bitmap_left
    if b.rows :
        data = array.array('B', b.buffer)
        mask = QtGui.QImage(data, b.width, b.rows, b.pitch, QtGui.QImage.Format_Indexed8)
        image = QtGui.QImage(b.width, b.rows, QtGui.QImage.Format_Mono)
        image.fill(0)
        image.setAlphaChannel(mask)
        pixmap = QtGui.QPixmap(image)
    else :
        pixmap = None
    return (pixmap, left, top)

class GlyphItem(object) :

    def __init__(self, face, gid, height = 40) :
        face.set_char_size(height = int(height * 64))
        (self.pixmap, self.left, self.top) = ftGlyph(face, gid)
        n = ctypes.create_string_buffer(64)
        freetype.FT_Get_Glyph_Name(face._FT_Face, gid, n, ctypes.sizeof(n))
        self.name = n.value

class Glyph(gdlGlyph, DataObj) :

    def __init__(self, name, gid = 0, item = None) :
        super(Glyph, self).__init__(name, gid)
        self.item = item
        self.isHigh = False
        self.justifies = []

    def __str__(self) :
        return self.psname

    def attribModel(self) :
        res = []
        for a in ['psname', 'gid'] :
            res.append(Attribute(a, self.__getattribute__, None, False, a)) # read-only
        res.append(Attribute('GDLName', self.GDLName, self.setGDL))
        for a in ['uid', 'comment'] :
            res.append(Attribute(a, self.__getattribute__, self.__setattr__, False, a))
        for a in sorted(self.properties.keys()) :
            res.append(Attribute(a, self.getproperty, self.setproperty, False, a))
        for a in sorted(self.gdl_properties.keys()) :
            res.append(Attribute(a, self.getgdlproperty, self.setgdlproperty, False, a))
        resAttrib = AttribModel(res)
        pres = []
        for k in self.anchors.keys() :
            pres.append(Attribute(k, self.getpoint, self.setpoint, False, k))
        pAttrib = AttribModel(pres, resAttrib)
        resAttrib.add(Attribute('points', None, None, True, pAttrib))
        if len(self.justifies) :
            jAttrib = AttribModel([], resAttrib)
            for (i, j) in enumerate(self.justifies) :
                jlevel = []
                for k in j.keys() :
                    jlevel.append(Attribute(k, self.getjustify, None, False, i, k))
                lAttrib = AttribModel(jlevel, jAttrib)
                jAttrib.add(Attribute(str(i), None, None, True, lAttrib))
            resAttrib.add(Attribute('Justify', None, None, True, jAttrib))
        return resAttrib

    def getproperty(self, key) :
        return self.properties[key]

    def setproperty(self, key, value) :
        if value == None :
            del self.properties[key]
        else :
            self.properties[key] = value

    def getgdlproperty(self, key) :
        return self.gdl_properties[key]

    def setgdlproperty(self, key, value) :
        if value == None :
            del self.gdl_properties[key]
        else :
            self.gdl_properties[key] = value

    def getpoint(self, key) :
        return str(self.anchors[key])

    def setpoint(self, key, value) :
        if value == None :
            del self.anchors[key]
        elif value == "" :
            self.anchors[key] = (0, 0)
        else :
            self.anchors[key] = map(int, re.split(r",\s*", value[1:-1]))

    def setpointint(self, key, x, y) :
        if key in self.anchors :
            if x is None : x = self.anchors[key][0]
            if y is None : y = self.anchors[key][1]
        self.anchors[key] = (x, y)

    def getjustify(self, level, name) :
        if level >= len(self.justifies) or name not in self.justifies[level] : return None
        return self.justifies[level][name]

    def setjustify(self, level, name, val) :
        if level >= len(self.justifies) :
            self.justifies.extend(({},) * (level - len(self.justifies) + 1))
        self.justifies[level][name] = val

    def addClass(self, name) :
        if name not in self.classes :
            self.classes.add(name)
            self.properties['classes'] = "  ".join(sorted(self.classes))

    def removeClass(self, name) :
        if name in self.classes :
            self.classes.discard(name)
            self.properties['classes'] = "  ".join(sorted(self.classes))

    def highlight(self, value) :
        self.isHigh = value

    def isHighlighted(self) :
        return self.isHigh
