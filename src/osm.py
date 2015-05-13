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

        self.header = """
<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
<bounds minlat="%s" minlon="%s" maxlat="%s" maxlon="%s" />
""" % (str(self.bounds[0]), str(self.bounds[1]), str(self.bounds[2]), str(self.bounds[3]))
        self.footer = "</osm>"

    def export(self, format="osm"):
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

        osm = self.header + "\n".join(node_list) + "\n" + "\n".join(way_list) + "\n" + self.footer

        return osm