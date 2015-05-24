class Way(object):
    def __init__(self, wid=None, nids=(), type=None):
        if wid is None:
            self.id = id(self)
        else:
            self.id = wid
        self.nids = nids
        self.type = type
        return

    def get_node_ids(self):
        return self.nids

class Ways(object):
    def __init__(self):
        self.ways = {}
        self.intersection_node_ids = []

    def add(self, wid, way):
        self.ways[wid] = way

    def get(self, wid):
        return self.ways[wid]

    def get_list(self):
        return self.ways.values()

    def remove(self, wid):
        # http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        del self.ways[wid]
        return

    def set_intersection_node_ids(self, nids):
        self.intersection_node_ids = nids

# Notes on inheritance
# http://stackoverflow.com/questions/576169/understanding-python-super-with-init-methods
class Street(Way):
    def __init__(self, wid=None, nids=(), type=None):
        super(Street, self).__init__(wid, nids, type)
        self.sidewalk_ids = []  # Keep track of which sidewalks were generated from this way

    def append_sidewalk_id(self, way_id):
        self.sidewalk_ids.append(way_id)
        return self

    def get_sidewalk_ids(self):
        return self.sidewalk_ids

class Streets(Ways):
    def __init__(self):
        super(Streets, self).__init__()

class Sidewalk(Way):
    def __init__(self, wid=None, nids=(), type=None):
        super(Sidewalk, self).__init__(wid, nids, type)

    def set_street_id(self, street_id):
        """  Set the parent street id """
        self.street_id = street_id
        return

class Sidewalks(Ways):
    def __init__(self):
        super(Sidewalks, self).__init__()
        self.street_id = None

