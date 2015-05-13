from latlng import LatLng
import numpy as np
import math


class Node(LatLng):
    def __init__(self, nid=None, latlng=None):
        self.latlng = latlng

        if nid is None:
            self.id = id(self)
        else:
            self.id = nid

        self.way_ids = []
        self.sidewalk_nodes = {}
        self.prev = {}
        self.next = {}
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

    def is_intersection(self):
        return len(self.way_ids) > 1

    def has_sidewalk_nodes(self):
        return len(self.sidewalk_nodes) > 0

    def get_connected(self, way_id=None):
        return self.next.values() + self.prev.values()

    def get_prev(self, way_id):
        return self.prev[way_id]

    def get_next(self, way_id):
        return self.next[way_id]

    def get_way_ids(self):
        return self.way_ids

    def set_prev(self, way_id, prev):
        self.prev[way_id] = prev

    def set_next(self, way_id, next):
        self.next[way_id] = next

    def vector(self):
        return np.array(self.latlng.location())

    def vector_to(self, node, normalize=True):
        vec = np.array(node.latlng.location()) - np.array(self.latlng.location())
        if normalize:
            vec = vec / np.linalg.norm(vec)
        return vec


class Nodes():
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
