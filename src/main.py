from utilities import WaySearcher, LatLng
import logging as log
import math
import numpy as np

from itertools import islice

try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET


log.basicConfig(format="", level=log.DEBUG)

# Itertools
# https://docs.python.org/2/library/itertools.html#recipes
# Helper sliding window iterater method
# See: http://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python
from itertools import tee, izip
def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result # print "Way Id:", way.id, way.nids
    return


class Node(LatLng):
    def __init__(self, nid=None, latlng=None):
        self.latlng = latlng

        if nid is None:
            self.id = id(self)
        else:
            self.id = nid

        self.way_ids = []
        self.sidewalk_nodes = []
        return

    def __str__(self):
        return "Node object, id: " + str(self.id)

    def append_way(self, wid):
        self.way_ids.append(wid)
        return

    def create_sidewalk_nodes(self, nodes, ways):
        adj_node_ids = []
        for wid in self.way_ids:
            way = ways.get(wid)
            node_idx = way.nids.index(self.id)

            if node_idx == 0:
                # The first node
                adj_node_ids.append(way.nids[1])
            elif node_idx == len(way.nids) - 1:
                # The last node
                adj_node_ids.append(way.nids[-2])
            else:
                adj_node_ids.append(way.nids[node_idx - 1])
                adj_node_ids.append(way.nids[node_idx + 1])

        adj_nodes = [nodes.get(nid) for nid in adj_node_ids]
        def cmp(n1, n2):
            angle = self.angle_between(n1, n2)
            if angle < 0:
                return -1
            elif angle == 0:
                return 0
            else:
                return 1
        adj_nodes = sorted(adj_nodes, cmp=cmp)

        lat_self, lng_self = self.location()
        for n1, n2 in window(adj_nodes, 2):
            v1 = self.vector_to(n1, normalize=True)
            v2 = self.vector_to(n2, normalize=True)
            v = v1 + v2
            v_norm = v / np.linalg.norm(v)
            # Todo: Add weighted v_norm to current location

        # Todo. Do the same thing as what I did in the for loop above for the last pair
        lat1, lng1 = adj_nodes[-1].location()
        lat2, lng2 = adj_nodes[0].location()
        return

    def vector_to(self, node, normalize=True):
        vec = np.array(node.latlng.location) - np.array(self.latlng.location)
        if normalize:
            vec = vec / np.linalg.norm(vec)
        return vec

    def angle_to(self, node):
        y_node, x_node = node.latlng.location(radian=True)
        y_self, x_self = self.latlng.location(radian=True)
        return math.atan2(y_node - y_self, x_node - x_self)

    def angle_between(self, node1, node2):
        y_node1, x_node1 = node1.latlng.location(radian=True)
        y_node2, x_node2 = node2.latlng.location(radian=True)
        return math.atan2(y_node2 - y_node1, x_node2 - x_node1)


    def is_intersection(self):
        return len(self.way_ids) > 1

    def has_sidewalk_nodes(self):
        return len(self.sidewalk_nodes) > 0


class Nodes():
    def __init__(self):
        self.nodes = {}
        return

    def add(self, nid, node):
        self.nodes[nid] = node
        return

    def get(self, nid):
        return self.nodes[nid]

    def get_list(self):
        return self.nodes.values()


class Way():
    def __init__(self, wid=None, nids=[], type=None):
        if wid is None:
            self.id = id(self)
        else:
            self.id = wid
        self.nids = nids
        self.type = type
        return


class Ways():
    def __init__(self):
        self.ways = {}

    def add(self, wid, way):
        self.ways[wid] = way

    def get(self, wid):
        return self.ways[wid]

    def get_list(self):
        return self.ways.values()


def parse(filename):
    """
    Parse a OSM file
    """
    with open(filename, "rb") as osm:
        # Find element
        # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
        tree = ET.parse(osm)

        nodes_tree = tree.findall(".//node")
        ways_tree = tree.findall(".//way")
        nodes = Nodes()

        for node in nodes_tree:
            mynode = Node(node.get("id"), LatLng(node.get("lat"), node.get("lon")))
            nodes.add(node.get("id"), mynode)

        # Parse ways and find streets that has the following tags
        ways = Ways()
        valid_highways = set(['primary', 'secondary', 'tertiary', 'residential'])
        for way in ways_tree:
            highway_tag = way.find(".//tag[@k='highway']")
            # print type(highway_tag)
            if highway_tag is not None and highway_tag.get("v") in valid_highways:
                # print highway_tag.get("v"), way
                node_elements = filter(lambda elem: elem.tag == "nd", list(way))
                nids = [node.get("ref") for node in node_elements]

                # Todo: Nodes that are too close to each other should be filtered out.

                myway = Way(way.get("id"), nids)
                ways.add(way.get("id"), myway)

    return nodes, ways


def find_intersections(nodes, ways):
    """
    Find intersections
    :param nodes:
    :param ways:
    :return:
    """
    for way in ways.get_list():
        for nid in way.nids:
            nodes.get(nid).append_way(way.id)


def print_intersections():
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            print str(location[0]) + "," + str(location[1])
    return


def make_sidewalk_points(prev_node, curr_node, next_node):
    import numpy as np
    prev_latlng = np.array(prev_node.latlng.location())
    curr_latlng = np.array(curr_node.latlng.location())
    next_latlng = np.array(next_node.latlng.location())

    v_cp = prev_latlng - curr_latlng
    v_cp_n = v_cp / np.linalg.norm(v_cp)
    v_cn = next_latlng - curr_latlng
    v_cn_n = v_cn / np.linalg.norm(v_cn)
    v_sidewalk = v_cp_n + v_cn_n
    v_sidewalk_n = v_sidewalk / np.linalg.norm(v_sidewalk)

    p1 = curr_latlng + 0.00005 * v_sidewalk_n
    p2 = curr_latlng - 0.00005 * v_sidewalk_n
    latlng1 = LatLng(math.degrees(p1[0]), math.degrees(p1[1]))
    latlng2 = LatLng(math.degrees(p2[0]), math.degrees(p2[1]))

    p_sidewalk_1 = Node(None, latlng1)
    p_sidewalk_2 = Node(None, latlng2)

    return p_sidewalk_1, p_sidewalk_2


def main(nodes, ways):
    # Find intersections
    find_intersections(nodes, ways)
    #print_intersections()  # Debug



    # Go through each street and create sidewalks on both sides of the road.
    sidewalks = Ways()
    for way in ways.get_list():
        sidewalk_1 = Way()
        sideawlk_2 = Way()
        prev_node = None

        # First node
        prev_node = None
        curr_node = nodes.get(way.nids[0])
        next_node = nodes.get(way.nids[1])
        # Todo. Do stuff

        # The rest of the points
        for prev_nid, curr_nid, next_nid in window(way.nids, n=3):
            prev_node = nodes.get(prev_nid)
            curr_node = nodes.get(curr_nid)
            next_node = nodes.get(next_nid)

            if curr_node.is_intersection():
                print "Intersection"
                if not curr_node.has_sidewalk_nodes():
                    curr_node.create_sidewalk_nodes(nodes, ways)

            else:
                #print "Not Intersection"
                make_sidewalk_points(prev_node, curr_node, next_node)
                # p1, p2 = get_non_intersection(prev_node, curr_node, next_node)

            # print prev_nid, curr_nid, next_nid

        # The final point
        prev_node = nodes.get(way.nids[-2])
        curr_node = nodes.get(way.nids[-1])
        next_node = None
        # Todo. Do stuff
    return

if __name__ == "__main__":
    filename = "../resources/map2.osm"
    nodes, ways = parse(filename)
    main(nodes, ways)