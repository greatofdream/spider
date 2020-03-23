#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import xml.sax
import sys
import string

class GeometryHandler(xml.sax.ContentHandler):
    def __init__(self, foname):
        self.CurrentData = ""
        self.CurrentIndex = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.pmtData = []
        self.fopt = open(foname,'w')
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if self.CurrentData == "physvol":
            self.CurrentIndex = int(attributes['name'].replace('PMT_',''))
            # print("begin{}".format(self.CurrentIndex))
        elif self.CurrentData == "position":
            self.x = float(attributes['x'])*1000
            self.y = float(attributes['y'])*1000
            self.z = float(attributes['z'])*1000
    def endElement(self, tag):
        if self.CurrentData == "position":
            self.pmtData.append([self.CurrentIndex, self.x, self.y, self.z])
            #self.fopt.write('{} {} {} {}\n'.format(self.CurrentIndex, self.x, self.y, self.z))
            # print("end{}".format(self.CurrentIndex))
        self.CurrentData = ""
    '''
    def characters(self, content):
        if self.CurrentData == "position":
            print(content)
    '''
    def sort(self):
        self.pmtData.sort(key=lambda e:e[0])
    def write(self):
        for e in self.pmtData:
            self.fopt.write('{} {} {} {}\n'.format(e[0], e[1],e[2],e[3]))
        self.fopt.close() 
if (__name__ == "__main__"):
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    finame = sys.argv[1]
    foname = sys.argv[2]
    Handler = GeometryHandler(foname)
    parser.setContentHandler( Handler)
    with open(finame) as ipt:
        xmlData = ipt.read()
    xml.sax.parseString('<root>{}</root>'.format(xmlData), Handler)
    Handler.sort()
    Handler.write()
    #print(Handler.pmtData)
