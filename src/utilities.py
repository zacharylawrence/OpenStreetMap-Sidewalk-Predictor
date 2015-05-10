from math import radians
from imposm.parser import OSMParser
from shapely.geometry import LineString
from itertools import islice

import pprint

try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET

pp = pprint.PrettyPrinter(indent=2)

# Itertools
# https://docs.python.org/2/library/itertools.html#recipes
# Helper sliding window iterater method
# See: http://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python
def window(seq, n=2, padding=None):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "

    # it = iter(seq)
    if padding is not None:
        seq = [None for i in range(padding)] + list(seq) + [None for i in range(padding)]
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result # print "Way Id:", way.id, way.nids
    return

# class LatLng():
#     def __init__(self, lat, lng, node_id=None):
#         self.lat = float(lat)
#         self.lng = float(lng)
#         self.node_id = node_id
#         return
#
#     def location(self, radian=True):
#         if radian:
#             return (radians(self.lat), radians(self.lng))
#         else:
#             return (self.lat, self.lng)
#
#     def __str__(self):
#         return str(self.lat) + "," + str(self.lng)


class MyLineString(LineString):
    def __init__(self, coordinates=None, latlngs=None):
        super(MyLineString, self).__init__(coordinates)
        self.latlngs = latlngs
        self.nearby = []


class MyStreet():
    def __init__(self, linestrings=None):
        self.linestrings = linestrings


class WaySearcher(object):
    def __init__(self, filename):
        self.filename = filename
        self.ways_found = []
        self.way_nodes = []
        self.key_values = []

    def find_ways(self, key_values):
        self.key_values = key_values
        p = OSMParser(concurrency=4, ways_callback=self.way_callback)
        p.parse(self.filename)

        self.ways_found = list(set(self.ways_found)) # delete duplicates.
        self.way_nodes = list(set(self.way_nodes))

        return self

    def key_values_exist(self, tags):
        """
        This method
        """
        for key, value in self.key_values:
            if key in tags:
                # Check if the value is iterable
                # http://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
                if hasattr(value, '__iter__'):
                    flag = False
                    for v in value:
                        if v is None or v == tags[key]:
                            flag = True
                    if not flag:
                        return False
                else:
                    if value and value != tags[key]:
                        # If value is not None and it does not agree with tags[key],
                        return False
            else:
                return False

        return True

    def get_osm(self):
        ret = "<osm>\n"
        with open(self.filename, "rb") as osm:
            # Find element
            # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
            tree = ET.parse(osm)
            # print tree.find(".//way[@id='%d']" % self.ways_found[0])
            ret += ET.tostring(tree.find(".//bounds"))
            for node_id in self.way_nodes:
                ret += ET.tostring(tree.find(".//node[@id='%d']" % node_id))
            for way_id in self.ways_found:
                ret += ET.tostring(tree.find(".//way[@id='%d']" % way_id))
        ret += "</osm>"
        return ret

    def get_ways(self):
        return self.ways_found

    def way_callback(self, ways):
        """
        This method returns ids of  elements that contains all key-value pairs in key_values
        """

        if ways:
            for way in ways:
                if self.key_values_exist(way[1]):
                    self.ways_found.append(way[0])
                    self.way_nodes += way[2]
            #self.ways_found += [way[0] for way in ways ]
            #self.way_nodes += [way[2]]



        #print self.ways_found
        return


if __name__ == "__main__":
    filename = "../resources/MarylandAvenueNortheast.osm"
    searcher = WaySearcher(filename)
    print searcher.find_ways((("highway", None), ("name", "Maryland Avenue Northeast"))).get_ways()
