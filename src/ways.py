
class Way():
    def __init__(self, wid=None, nids=[], type=None):
        if wid is None:
            self.id = id(self)
        else:
            self.id = wid
        self.nids = nids
        self.type = type
        self.child_way_ids = []  # Keep track of which sidewalks were generated from this way
        self.parent_way_id = None  # Keep track of the parent street
        return

    def append_child_way_id(self, way_id):
        self.child_way_ids.append(way_id)
        return

    def get_child_way_ids(self):
        return self.child_way_ids

    def get_node_ids(self):
        return self.nids

    def set_parent_way_id(self, way_id):
        self.parent_way_id = way_id
        return


class Ways():
    def __init__(self):
        self.ways = {}
        self.intersection_node_ids = []

    def add(self, wid, way):
        self.ways[wid] = way

    def get(self, wid):
        return self.ways[wid]

    def get_list(self):
        return self.ways.values()
