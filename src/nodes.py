from latlng import LatLng
from ways import Way, Ways
import numpy as np

class Node(LatLng):
    def __init__(self, nid=None, latlng=None):
        self.latlng = latlng

        if nid is None:
            self.id = id(self)
        else:
            self.id = nid

        self.way_ids = []
        self.sidewalk_nodes = []

        self.prev = {}
        self.next = {}
        return

    def __str__(self):
        return "Node object, id: " + str(self.id)

    def set_prev(self, way_id, prev):
        self.prev[way_id] = prev
        return

    def set_next(self, way_id, next):
        self.next[way_id] = next
        return

    def get_prev(self, way_id):
        return self.prev[way_id]

    def get_next(self, way_id):
        return self.next[way_id]

    def append_way(self, wid):
        self.way_ids.append(wid)
        return

    def create_sidewalk_nodes(self, **kwargs):
        if self.has_sidewalk_nodes():
            return

        if not self.is_intersection():
            # print "Not Intersection"
            nodes_array = kwargs["nodes_array"]
            wid = self.way_ids[0]
            idx = ways.get(wid).nids.index(self.id)
            prev_idx = ways.get(wid).nids[idx - 1]
            next_idx = ways.get(wid).nids[idx + 1]
            prev_node = nodes.get(prev_idx)
            next_node = nodes.get(next_idx)

            prev_latlng = np.array(prev_node.latlng.location())
            curr_latlng = np.array(self.latlng.location())
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
            self.sidewalk_nodes.append(p_sidewalk_1)
            self.sidewalk_nodes.append(p_sidewalk_2)
        else:
            nodes = kwargs["nodes"]
            ways = kwargs["ways"]
            adj_node_ids = []

            if len(adj_node_ids) > 3:
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
                    angle1 = self.angle_to(n1)
                    angle2 = self.angle_to(n2)
                    if angle1 < angle2:
                        return -1
                    elif angle1 == angle2:
                        return 0
                    else:
                        return 1
                adj_nodes = sorted(adj_nodes, cmp=cmp)

                v_curr = np.array(self.latlng.location())

                for n1, n2 in window(adj_nodes, 2):
                    v1 = self.vector_to(n1, normalize=True)
                    v2 = self.vector_to(n2, normalize=True)
                    v = v1 + v2
                    v_norm = v / np.linalg.norm(v)
                    v_new = v_curr + v_norm * 0.000001

                    latlng_new = LatLng(math.degrees(v_new[0]), math.degrees(v_new[1]))
                    node_new = Node(None, latlng_new)
                    self.sidewalk_nodes.append(node_new)

                n1 = adj_nodes[-1]
                n2 = adj_nodes[0]
                v1 = self.vector_to(n1, normalize=True)
                v2 = self.vector_to(n2, normalize=True)
                v = v1 + v2
                v_norm = v / np.linalg.norm(v)
                v_new = np.array(self.latlng.location()) + v_norm * 0.000001
                latlng_new = LatLng(math.degrees(v_new[0]), math.degrees(v_new[1]))
                node_new = Node(None, latlng_new)
                self.sidewalk_nodes.append(node_new)

        return

    def vector(self):
        return np.array(self.latlng.location())

    def vector_to(self, node, normalize=True):
        vec = np.array(node.latlng.location()) - np.array(self.latlng.location())
        if normalize:
            vec = vec / np.linalg.norm(vec)
        return vec

    def angle_to(self, node):
        y_node, x_node = node.latlng.location(radian=True)
        y_self, x_self = self.latlng.location(radian=True)
        return math.atan2(y_node - y_self, x_node - x_self)

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
        if nid in self.nodes:
            return self.nodes[nid]
        else:
            return None

    def get_list(self):
        return self.nodes.values()
