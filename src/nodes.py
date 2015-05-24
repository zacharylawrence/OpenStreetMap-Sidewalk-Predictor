from latlng import LatLng
import numpy as np
import math
import logging as log

class Node(object):
    def __init__(self, nid=None, latlng=None):
        self.latlng = latlng  # Note: Would it be cleaner to inherit LatLng?

        if nid is None:
            self.id = id(self)
        else:
            self.id = nid

        self.way_ids = []
        self.sidewalk_nodes = {}
        self.min_intersection_cardinality = 2
        return

    def __str__(self):
        return "Node object, id: " + str(self.id) + ", latlng: " + str(self.latlng.location(radian=False))

    def angle_to(self, node):
        y_node, x_node = node.latlng.location(radian=True)
        y_self, x_self = self.latlng.location(radian=True)
        return math.atan2(y_node - y_self, x_node - x_self)

    def append_sidewalk_node(self, way_id, node):
        self.sidewalk_nodes.setdefault(way_id, []).append(node)

    def append_way(self, wid):
        self.way_ids.append(wid)

    def distance_to(self, node):
        return self.latlng.distance_to(node.latlng)

    def is_intersection(self):
        return len(self.way_ids) >= self.min_intersection_cardinality

    def has_sidewalk_nodes(self):
        return len(self.sidewalk_nodes) > 0

    def get_way_ids(self):
        return self.way_ids

    def get_sidewalk_nodes(self, wid):
        return self.sidewalk_nodes[wid]

    def remove_way_id(self, wid):
        self.way_ids.remove(wid)
        return

    def vector(self):
        return np.array(self.latlng.location())

    def vector_to(self, node, normalize=True):
        vec = np.array(node.latlng.location()) - np.array(self.latlng.location())
        if normalize:
            vec = vec / np.linalg.norm(vec)
        return vec


class Nodes(object):
    def __init__(self):
        self.nodes = {}
        return

    def add(self, nid, node):
        self.nodes[nid] = node
        return

    def get(self, nid):
        if nid in self.nodes:
            return self.nodes[nid]
        else:
            return None

    def get_list(self):
        return self.nodes.values()

    def remove(self, nid):
        # http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        del self.nodes[nid]
        return

def print_intersections(nodes):
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            log.debug(str(location[0]) + "," + str(location[1]))
    return