from latlng import LatLng
from nodes import Node, Nodes
from ways import Way, Ways
from utilities import window
from osm import OSM

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
            if nodes.get(nid).is_intersection() and nid not in ways.intersection_node_ids:
                ways.intersection_node_ids.append(nid)

    return nodes, ways


def print_intersections(nodes):
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            log.debug(str(location[0]) + "," + str(location[1]))
    return


def make_sidewalk_nodes(way_id, prev_node, curr_node, next_node):
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

    curr_latlng = np.array(curr_node.latlng.location())

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

    curr_node.append_sidewalk_node(way_id, p_sidewalk_1)
    curr_node.append_sidewalk_node(way_id, p_sidewalk_2)

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

            n1, n2 = make_sidewalk_nodes(way.id, prev_node, curr_node, next_node)

            sidewalk_nodes.add(n1.id, n1)
            sidewalk_nodes.add(n2.id, n2)

            sidewalk_1_nodes.append(n1)
            sidewalk_2_nodes.append(n2)
            #log.debug(n1.latlng.location(radian=False))
            #log.debug(n2.latlng.location(radian=False))

        # Keep track of parent-child relationship between streets and sidewalks.
        # And set nodes' adjacency information
        sidewalk_1 = Way(None, [node.id for node in sidewalk_1_nodes], "footway")
        sidewalk_2 = Way(None, [node.id for node in sidewalk_2_nodes], "footway")
        sidewalk_1.set_parent_way_id(way.id)
        sidewalk_2.set_parent_way_id(way.id)
        way.append_child_way_id(sidewalk_1.id)
        way.append_child_way_id(sidewalk_2.id)
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


def make_intersection_nodes(nodes, sidewalk_nodes, ways, sidewalk_ways):
    # Some helper functions
    def make_intersection_node(node, n1, n2, angle=None):
        const = 0.000001
        if n2 is None and angle is not None:
            v1 = node.vector_to(n1, normalize=True)
            rot_mat = np.array([(math.cos(angle), -math.sin(angle)), (math.sin(angle), math.cos(angle))])
            v_norm = rot_mat.dot(v1)
            v_new = v_curr + v_norm * const
            latlng_new = LatLng(math.degrees(v_new[0]), math.degrees(v_new[1]))
            return Node(None, latlng_new)
        else:
            v1 = node.vector_to(n1, normalize=True)
            v2 = node.vector_to(n2, normalize=True)
            v = v1 + v2
            v_norm = v / np.linalg.norm(v)
            v_new = v_curr + v_norm * const
            latlng_new = LatLng(math.degrees(v_new[0]), math.degrees(v_new[1]))
            return Node(None, latlng_new)

    def cmp(n1, n2):
        angle1 = intersection_node.angle_to(n1)
        angle2 = intersection_node.angle_to(n2)
        if angle1 < angle2:
            return -1
        elif angle1 == angle2:
            return 0
        else:
            return 1

    intersection_node_ids = ways.intersection_node_ids
    intersection_nodes = [nodes.get(nid) for nid in intersection_node_ids]

    # Create sidewalk nodes for each intersection node and overwrite the adjacency information
    for intersection_node in intersection_nodes:
        way_ids = intersection_node.get_way_ids()
        adj_nodes = []
        for wid in way_ids:
            if intersection_node.get_next(wid) is not None:
                adj_nodes.append(intersection_node.get_next(wid))
            if intersection_node.get_prev(wid) is not None:
                adj_nodes.append(intersection_node.get_prev(wid))

        adj_nodes = sorted(adj_nodes, cmp=cmp)
        v_curr = intersection_node.vector()


        # Creat new intersection sidewalk nodes
        # Record from which street nodes each intersection node is created with source_table
        source_table = {}
        new_intersection_sidewalk_nodes = []
        if len(adj_nodes) == 3:
            # Todo. Take care of the case where len(adj_nodes) == 3
            continue
            # print len(adj_nodes)
            #
            # vecs = []
            # for n in adj_nodes:
            #     vecs.append(intersection_node.vector_to(n))
            #
            # def angle(v1, v2):
            #     return np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            # max_angle_idx = np.array([angle(vecs[i], vecs[i - 1]) for i in range(len(vecs))]).argmax()
            # max_angle = angle(vecs[max_angle_idx], vecs[max_angle_idx - 1])
            #
            # for i in range(len(adj_nodes)):
            #     n1 = adj_nodes[i-1]
            #     n2 = adj_nodes[i]
                # if i == max_angle_idx:
                #     node_new = make_intersection_node(intersection_node, n2, n2=None, angle=max_angle / 2 - 0.00000001)
                # else:
                #     node_new = make_intersection_node(intersection_node, n1, n2)
                # node_new = make_intersection_node(intersection_node, n1, n2)
                # sidewalk_nodes.add(node_new.id, node_new)
                # new_intersection_sidewalk_nodes.append(node_new)
                # source_table[node_new.id] = [intersection_node, n1, n2]

        else:
            for n1, n2 in window(adj_nodes, 2):
                node_new = make_intersection_node(intersection_node, n1, n2)
                sidewalk_nodes.add(node_new.id, node_new)
                new_intersection_sidewalk_nodes.append(node_new)
                source_table[node_new.id] = [intersection_node, n1, n2]

            n1 = adj_nodes[-1]
            n2 = adj_nodes[0]
            node_new = make_intersection_node(intersection_node, n1, n2)
            sidewalk_nodes.add(node_new.id, node_new)
            new_intersection_sidewalk_nodes.append(node_new)
            source_table[node_new.id] = [intersection_node, n1, n2]

        # Add the cross walk to the data structure
        # crosswalk = Way(None, new_intersection_sidewalk_nodes, "crosswalk")
        # sidewalk_ways.add(crosswalk.id, crosswalk)

        # Connect the new intersection sidewalk nodes with appropriate sidewalk nodes
        for new_node_id in source_table:
            # Get the intersection node and two nodes that created the intersection sidewalk node
            ni, n1, n2 = source_table[new_node_id]
            ni_s = sidewalk_nodes.get(new_node_id)
            v_ni_s = ni.vector_to(ni_s)  # A vector to the intersection sidewalk node

            for n_adj in [n1, n2]:
                v_n_adj = ni.vector_to(n_adj)  # A vector to n1
                shared_ways = set(intersection_node.way_ids) & set(n_adj.way_ids)
                shared_way_id = list(shared_ways)[0]

                # Get a pair of vectors to two sidewalk nodes created from n1
                n_adj_s1, n_adj_s2 = n_adj.sidewalk_nodes[shared_way_id]
                v_n_adj_s1 = intersection_node.vector_to(n_adj_s1)

                # Check which one of n1_s1 and n1_s2 are on the same side of the road with ni_s
                # If the rotation (cross product) from v_n1 to v_ni_s is same as v_n1 to v_n1_s1, then
                # n1_s1 should be on the same side. Otherwise, n1_s1 should be on the same side with ni_s.
                if np.cross(v_n_adj, v_ni_s) * np.cross(v_n_adj, v_n_adj_s1) > 0:
                    n_adj_s_temp = n_adj_s1
                else:
                    n_adj_s_temp = n_adj_s2

                # Connect n1_s1 with temp_node
                n_temp_connected = n_adj_s_temp.get_connected()
                ni_all_sidewalk = [item for sublist in ni.sidewalk_nodes.values() for item in sublist]
                if len(set(n_temp_connected) & set(ni_all_sidewalk)) > 0:
                    n_target = list(set(n_temp_connected) & set(ni_all_sidewalk))[0]
                    shared_sidewalk = set(n_adj_s_temp.way_ids) & set(n_target.way_ids)
                    shared_sidewalk_id = list(shared_sidewalk)[0]

                    sidewalk = sidewalk_ways.get(shared_sidewalk_id)
                    if n_target.get_prev(shared_sidewalk_id) == n_adj_s_temp:
                        ni_s.set_prev(shared_sidewalk_id, n_adj_s_temp)
                        ni_s.set_next(shared_sidewalk_id, n_target)
                        n_adj_s_temp.set_next(shared_sidewalk_id, ni_s)
                        sidewalk.nids.insert(sidewalk.nids.index(n_target.id), ni_s.id)
                    else:
                        ni_s.set_next(shared_sidewalk_id, n_adj_s_temp)
                        ni_s.set_prev(shared_sidewalk_id, n_target)
                        n_adj_s_temp.set_prev(shared_sidewalk_id, ni_s)
                        sidewalk.nids.insert(sidewalk.nids.index(n_adj_s_temp.id), ni_s.id)

        # break
    return



def main(nodes, ways):
    sidewalk_nodes, sidewalk_ways = make_sidewalks(nodes, ways)
    make_intersection_nodes(nodes, sidewalk_nodes, ways, sidewalk_ways)
    osm = OSM(sidewalk_nodes, sidewalk_ways)
    output = osm.export()
    print output


if __name__ == "__main__":
    filename = "../resources/map2.osm"
    nodes, ways = parse(filename)
    main(nodes, ways)