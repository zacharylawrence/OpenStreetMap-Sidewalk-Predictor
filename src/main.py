from latlng import LatLng
from nodes import Node, Nodes
from ways import Way, Ways
from utilities import window

import logging as log
import math
import numpy as np


try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET


log.basicConfig(format="", level=log.DEBUG)




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
            if nodes.get(nid).is_intersection() and nid not in ways.intersection_nodes:
                ways.intersection_nodes.append(nid)

    return nodes, ways


def print_intersections():
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            print str(location[0]) + "," + str(location[1])
    return


def make_sidewalk_nodes(prev_node, curr_node, next_node):
    if prev_node is None:
        v = - curr_node.vector_to(next_node, normalize=False)
        vec_prev = curr_node.vector() + v
        latlng = LatLng(math.degrees(vec_prev[0]), math.degrees(vec_prev[1]))
        prev_node = Node(None, latlng)
    elif next_node is None:
        v = - curr_node.vector_to(prev_node, normalize=False)
        vec_next = curr_node.vector() + v
        latlng = LatLng(math.degrees(vec_next[0]), math.degrees(vec_next[1]))
        next_node = Node(None, latlng)

    prev_latlng = np.array(prev_node.latlng.location())
    curr_latlng = np.array(curr_node.latlng.location())
    next_latlng = np.array(next_node.latlng.location())

    v_cp_n = curr_node.vector_to(prev_node)
    v_cn_n = curr_node.vector_to(next_node)
    v_sidewalk = v_cp_n + v_cn_n

    if np.linalg.norm(v_sidewalk) < 0.0000000001:
        v_sidewalk_n = np.array([v_cn_n[1], - v_cn_n[0]])
    else:
        v_sidewalk_n = v_sidewalk / np.linalg.norm(v_sidewalk)

    # The constant is arbitrary.
    const = 0.000001
    p1 = curr_latlng + const * v_sidewalk_n
    p2 = curr_latlng - const * v_sidewalk_n
    latlng1 = LatLng(math.degrees(p1[0]), math.degrees(p1[1]))
    latlng2 = LatLng(math.degrees(p2[0]), math.degrees(p2[1]))

    p_sidewalk_1 = Node(None, latlng1)
    p_sidewalk_2 = Node(None, latlng2)

    # Figure out on which side you want to put each sidewalk node
    v_c1 = curr_node.vector_to(p_sidewalk_1)
    if np.cross(v_cn_n, v_c1) > 0:
        return p_sidewalk_1, p_sidewalk_2
    else:
        return p_sidewalk_2, p_sidewalk_1


def make_sidewalks(nodes, ways):
    # Go through each street and create sidewalks on both sides of the road.
    sidewalk_ways = Ways()
    sidewalk_nodes = Nodes()

    for way in ways.get_list():
        sidewalk_1_nodes = []
        sidewalk_2_nodes = []

        # Create sidewalk nodes
        for curr_nid in way.nids:
            curr_node = nodes.get(curr_nid)
            prev_node = curr_node.get_prev(way.id)
            next_node = curr_node.get_next(way.id)

            n1, n2 = make_sidewalk_nodes(prev_node, curr_node, next_node)

            sidewalk_nodes.add(n1.id, n1)
            sidewalk_nodes.add(n2.id, n2)

            sidewalk_1_nodes.append(n1)
            sidewalk_2_nodes.append(n2)
            print n1.latlng
            print n2.latlng

        # Set adjacency information
        sidewalk_1 = Way(None, [node.id for node in sidewalk_1_nodes])
        sidewalk_2 = Way(None, [node.id for node in sidewalk_2_nodes])
        for prev_nid, nid, next_nid in window(sidewalk_1.nids, 3, padding=1):
            curr_node = sidewalk_nodes.get(nid)
            curr_node.append_way(sidewalk_1.id)
            curr_node.set_prev(sidewalk_1.id, sidewalk_nodes.get(prev_nid))
            curr_node.set_next(sidewalk_1.id, sidewalk_nodes.get(next_nid))

        for prev_nid, nid, next_nid in window(sidewalk_2.nids, 3, padding=1):
            curr_node = sidewalk_nodes.get(nid)
            curr_node.append_way(sidewalk_2.id)
            curr_node.set_prev(sidewalk_2.id, sidewalk_nodes.get(prev_nid))
            curr_node.set_next(sidewalk_2.id, sidewalk_nodes.get(next_nid))

        # Add sidewalks to sidewalk_ways
        sidewalk_ways.add(sidewalk_1.id, sidewalk_1)
        sidewalk_ways.add(sidewalk_2.id, sidewalk_2)
    return sidewalk_nodes, sidewalk_ways

def main(nodes, ways):
    sidewalk_nodes, sidewalk_ways = make_sidewalks(nodes, ways)

if __name__ == "__main__":
    filename = "../resources/map2.osm"
    nodes, ways = parse(filename)
    main(nodes, ways)