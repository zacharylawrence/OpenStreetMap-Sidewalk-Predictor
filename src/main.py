from utilities import WaySearcher, LatLng
import logging as log


try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET


log.basicConfig(format="", level=log.DEBUG)


class Node(LatLng):
    def __init__(self, nid, latlng):
        self.latlng = latlng
        self.id = nid
        self.way_ids = []
        return

    def append_way(self, wid):
        self.way_ids.append(wid)
        return

    def is_intersection(self):
        return len(self.way_ids) > 1


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
    def __init__(self, wid, nids):
        self.id = wid
        self.nids = nids
        return

class Ways():
    def __init__(self):
        self.ways = {}

    def add(self, wid, way):
        self.ways[wid] = way

    def get_list(self):
        return self.ways.values()


def parse(filename):
    """
    :param filename:
    :return: Nodes and Ways
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


def main(nodes, ways):
    # Find intersections
    find_intersections(nodes, ways)

    #
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            print str(location[0]) + "," + str(location[1])

    return

if __name__ == "__main__":
    filename = "../resources/map2.osm"
    nodes, ways = parse(filename)
    main(nodes, ways)