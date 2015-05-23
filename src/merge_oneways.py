import numpy as np
import matplotlib.pyplot as plt
import pprint

from math import radians
from utilities import WaySearcher, LatLng, MyLineString, MyStreet
from scipy import spatial

from shapely.geometry import LineString

try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET

pp = pprint.PrettyPrinter(indent=2)



#
# class MyLineString(LineString):
#     def __init__(self, coordinates=None, latlngs=None):
#         super(MyLineString, self).__init__(coordinates)
#         self.latlngs = latlngs
#         self.nearby = []
#
#
# class MyStreet():
#     def __init__(self, linestrings=None):
#         self.linestrings = linestrings


def slice_street(street, threshold=5):
    """
    Slice a way into pieces if it is longer than a given threshold (in meters)
    """
    pass


def merge_oneways():
    """
    Merge one way segments that are parallel and close to each other.
    """
    # Find oneways
    # OpenStreetMap oneway: http://wiki.openstreetmap.org/wiki/Key:oneway
    oneways = searcher.find_ways((("highway", None), ("oneway", ("yes", "-1")))).get_ways()

    # Group oneways by street names

    filename = "../resources/ParallelLanes_01.osm"

    grouped_oneways = {}
    grouped_nodes = {}
    with open(filename, "rb") as osm:
        # Find element
        # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
        tree = ET.parse(osm)

        nodes = tree.findall(".//node")
        node_dict = {}
        for node in nodes:
            #node_dict[node.get("id")] = [radians(float(node.get("lon"))), radians(float(node.get("lat")))]
            node_dict[node.get("id")] = LatLng(node.get("lat"), node.get("lon"), node.get("id"))

        for way_id in oneways:
            way = tree.find(".//way[@id='%d']" % way_id)
            streetname_tag = way.find(".//tag[@k='name']")
            streetname = streetname_tag.get("v")
            grouped_oneways.setdefault(streetname, []).append(way)

    oneways = grouped_oneways["Maryland Avenue Northeast"]


    # Itertools
    # https://docs.python.org/2/library/itertools.html#recipes
    from itertools import tee, izip
    def pairwise(iterable):
        a, b = tee(iterable)
        next(b, None)
        return izip(a, b)

    # Create LineStrings: http://toblerity.org/shapely/manual.html
    streets = []
    for way in oneways:
        node_elements = filter(lambda elem: elem.tag == "nd", list(way))
        latlngs = [node_dict[node.get("ref")] for node in node_elements]

        # TODO: Split segments if they are too long. Implement slice_street().
        linestrings = [MyLineString([latlng1.location, latlng2.location]) for latlng1, latlng2 in pairwise(latlngs)]
        street = MyStreet(linestrings)
        streets.append(street)

    # Find distance between segments
    from itertools import combinations, product
    samples = []
    temp = {}
    for street_pair in combinations(streets, 2):
        street_a, street_b = street_pair[0], street_pair[1]
        street_a_idx, street_b_idx = streets.index(street_a), streets.index(street_b)
        temp[(street_a_idx, street_b_idx)] = 0

        for way_pair in product(*[street_a.linestrings, street_b.linestrings]):
            dist = way_pair[0].distance(way_pair[1])
            if dist < 1.0e-5:
                samples.append(dist)
                # print way_pair[0]
                way_pair[0].nearby.append(id(way_pair[1]))
                way_pair[1].nearby.append(id(way_pair[0]))
                temp[(street_a_idx, street_b_idx)] += 1

        temp[(street_a_idx, street_b_idx)] = float(temp[(street_a_idx, street_b_idx)]) / len(list(product(*[street_a.linestrings, street_b.linestrings])))

    pp.pprint(temp)


    # Show a histogram
    # import numpy as np
    # import matplotlib.pyplot as plt
    # import seaborn as sns
    # sns.set_palette("deep", desat=.6)
    # sns.set_context(rc={"figure.figsize": (8, 4)})
    # np.random.seed(9221999)
    # plt.hist(samples, 100)
    # plt.show()

    return

from math import radians, cos, sin, asin, sqrt


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal radians)

    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r

if __name__ == "__main__":
    filename = "../resources/ParallelLanes_01.osm"
    searcher = WaySearcher(filename)

    merge_oneways()
