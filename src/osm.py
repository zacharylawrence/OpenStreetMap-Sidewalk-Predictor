from xml.etree import cElementTree as ET

from latlng import LatLng
from nodes import Node, Nodes
from ways import Way, Ways, Street, Streets
from utilities import window

class OSM(object):
    def __init__(self, nodes, ways):
        self.nodes = nodes
        self.ways = ways
        self.bounds = [100000.0, 100000.0, -1.0, -1.0]  # min lat, min lng, max lat, and max lng

        for node in self.nodes.get_list():
            lat, lng = node.latlng.location(radian=False)
            if lat < self.bounds[0]:
                self.bounds[0] = lat
            elif lat > self.bounds[2]:
                self.bounds[2] = lat
            if lng < self.bounds[1]:
                self.bounds[1] = lng
            elif lng > self.bounds[3]:
                self.bounds[3] = lng

    def split_streets(self):
        """
        Split ways into pieces for preprocessing the OSM files.
        """
        new_streets = Streets()
        for way in self.ways.get_list():
            intersection_nids = [nid for nid in way.nids if self.nodes.get(nid).is_intersection()]
            intersection_indices = [way.nids.index(nid) for nid in intersection_nids]
            if len(intersection_indices) == 0:
                new_streets.add(way.id, way)
            else:
                if len(intersection_indices) == 1 and (intersection_indices[0] == 0 or intersection_indices[0] == len(way.nids)):
                    new_streets.add(way.id, way)
                if len(intersection_indices) == 2 and (intersection_indices[0] == 0 and intersection_indices[1] == len(way.nids)):
                    new_streets.add(way.id, way)
                else:
                    prev_idx = 0
                    for idx in intersection_indices:
                        if idx != 0 and idx != len(way.nids):
                            new_nids = way.nids[prev_idx:idx + 1]
                            new_way = Street(None, new_nids, way.type)
                            new_streets.add(new_way.id, new_way)
                            prev_idx = idx
                    new_nids = way.nids[prev_idx:]
                    new_way = Street(None, new_nids, way.type)
                    new_streets.add(new_way.id, new_way)
        self.ways = new_streets

        # Update the way_ids
        for node in self.nodes.get_list():
            # Now the minimum number of ways connected has to be 3 for the node to be an intersection
            node.way_ids = []
            node.min_intersection_cardinality = 3
        for street in self.ways.get_list():
            for nid in street.nids:
                nodes.get(nid).append_way(way.id)

        return self

    def merge_nodes(self, distance_threshold=0.025):
        """
        Merge nodes that are close to intersection nodes.
        """
        for street in self.ways.get_list():
            if len(street.nids) < 2:
                continue

            # print street.nids
            start = self.nodes.get(street.nids[0])
            end = self.nodes.get(street.nids[-1])
            # Merge the nodes around the beginning of the street
            for nid in street.nids[1:-1]:
                target = self.nodes.get(nid)
                distance = start.distance_to(target)
                if distance < distance_threshold:
                    street.nids.remove(nid)
                else:
                    break

            if len(street.nids) < 2:
                continue

            for nid in street.nids[-2:0:-1]:
                target = self.nodes.get(nid)
                distance = end.distance_to(target)
                if distance < distance_threshold:
                    street.nids.remove(nid)
                else:
                    break

            # print street.nids
        return self

    def export(self, format="osm"):
        header = """
<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
<bounds minlat="%s" minlon="%s" maxlat="%s" maxlon="%s" />
""" % (str(self.bounds[0]), str(self.bounds[1]), str(self.bounds[2]), str(self.bounds[3]))

        footer = "</osm>"
        node_list = []
        for node in self.nodes.get_list():
            lat, lng = node.latlng.location(radian=False)
            node_str = """<node id="%s" visible="true" user="test" lat="%s" lon="%s" />""" % (str(node.id), str(lat), str(lng))
            node_list.append(node_str)

        way_list = []
        for way in self.ways.get_list():
            way_str = """<way id="%s" visible="true" user="test">""" % (str(way.id))
            way_list.append(way_str)
            for nid in way.get_node_ids():
                nid_str = """<nd ref="%s" />""" % (str(nid))
                way_list.append(nid_str)

            if way.type is not None:
                tag = """<tag k="%s" v="%s" />""" % ("highway", way.type)
                way_list.append(tag)
            way_list.append("</way>")

        osm = header + "\n".join(node_list) + "\n" + "\n".join(way_list) + "\n" + footer

        return osm

    def filter(self):
        nids = []
        for way in self.ways.get_list():
            nids.extend(way.nids)
        nids = set(nids)

        new_nodes = Nodes()
        for nid in nids:
            new_nodes.add(nid, self.nodes.get(nid))

        self.nodes = new_nodes
        return self

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

    # Find intersections and store adjacency information
    for way in ways.get_list():
        # prev_nid = None
        for prev_nid, nid, next_nid in window(way.nids, 3, padding=1):
            # print prev_nid, nid, next_nid
            nodes.get(nid).append_way(way.id)

            nodes.get(nid).set_prev(way.id, nodes.get(prev_nid))
            nodes.get(nid).set_next(way.id, nodes.get(next_nid))
            if nodes.get(nid).is_intersection() and nid not in ways.intersection_node_ids:
                ways.intersection_node_ids.append(nid)

    return nodes, ways

if __name__ == "__main__":
    filename = "../resources/Simple4WayIntersection_01.osm"
    nodes, ways = parse(filename)
    obj = OSM(nodes, ways)
    print obj.filter().split_streets().merge_nodes().export()