
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
        self.intersection_nodes = []

    def add(self, wid, way):
        self.ways[wid] = way

    def get(self, wid):
        return self.ways[wid]

    def get_list(self):
        return self.ways.values()
