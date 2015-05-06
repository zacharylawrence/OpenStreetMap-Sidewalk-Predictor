import numpy as np
import matplotlib.pyplot as plt

from math import radians
from utilities import WaySearcher
from scipy import spatial

try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET


def merge_oneways():
    """
    Merge one way segments that are parallel and close to each other.
    """
    # Find oneways
    # OpenStreetMap oneway: http://wiki.openstreetmap.org/wiki/Key:oneway
    oneways = searcher.find_ways((("highway", None), ("oneway", ("yes", "-1")))).get_ways()

    # Group oneways by street names

    filename = "../resources/MarylandAvenueNortheast.osm"

    grouped_oneways = {}
    grouped_nodes = {}
    with open(filename, "rb") as osm:
        # Find element
        # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
        tree = ET.parse(osm)

        nodes = tree.findall(".//node")
        node_dict = {}
        for node in nodes:
            node_dict[node.get("id")] = [radians(float(node.get("lon"))), radians(float(node.get("lat")))]

        for way_id in oneways:
            way = tree.find(".//way[@id='%d']" % way_id)
            streetname_tag = way.find(".//tag[@k='name']")
            streetname = streetname_tag.get("v")
            grouped_oneways.setdefault(streetname, []).append(way)

    for streetname in grouped_oneways:
        node_id_list = []
        latlngs = []
        for way in grouped_oneways[streetname]:

            node_elements = filter(lambda elem: elem.tag == "nd", list(way))
            for node in node_elements:
                node_id = node.get("ref")

                # Append if there is no duplicate
                if node_id not in node_id_list:
                    node_id_list.append(node_id)
                    latlngs.append(node_dict[node_id])

        # TODO. Latlng points that are close to each other should be deleted
        np_latlngs = np.array(latlngs)

        # Voronoi
        # http://docs.scipy.org/doc/scipy-dev/reference/generated/scipy.spatial.Voronoi.html
        # vor = spatial.Voronoi(np_latlngs)
        # spatial.voronoi_plot_2d(vor)

        # Delaunay
        # http://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.spatial.Delaunay.html
        tri = spatial.Delaunay(np_latlngs)

        # tri.points[tri.simplices[0]] # Access triangles

        from numpy.linalg import norm

        def area(a, b, c):
            """
            Area of a triangle
            http://code.activestate.com/recipes/576896-3-point-area-finder/
            """
            return 0.5 * norm(np.cross(b - a, c - a))

        def aspect(a, b, c):
            """
            Aspect ratio of a triangle
            http://en.wikipedia.org/wiki/Types_of_mesh#Aspect_ratio
            """
            d1 = norm(a-b)
            d2 = norm(b-c)
            d3 = norm(c-a)
            a1 = d1 / d2 if d1 > d2 else d2 / d1
            a2 = d2 / d3 if d2 > d3 else d3 / d2
            a3 = d3 / d1 if d3 > d1 else d1 / d3
            return max((a1, a2, a3))

        def centroid(a, b, c):
            """
            Centroid of a triangle
            """
            return (a + b + c) / 3

        delete_indeces = []
        new_points = []
        for i, simplice in enumerate(tri.simplices):
            s = area(tri.points[simplice][0], tri.points[simplice][1], tri.points[simplice][2])
            asp = aspect(tri.points[simplice][0], tri.points[simplice][1], tri.points[simplice][2])
            if s < 1.26e-11 and asp < 3:
                delete_indeces.extend(simplice)
                new_point = centroid(tri.points[simplice][0], tri.points[simplice][1], tri.points[simplice][2])
                new_points.append(new_point)


        delete_indeces = set(delete_indeces)
        new_tri_points = [p for i, p in enumerate(tri.points) if i not in delete_indeces]
        new_tri_points.extend(new_points)
        new_tri_points = np.array(new_tri_points)

        #print np.array(new_points)
        plt.triplot(np_latlngs[:, 0], np_latlngs[:, 1], tri.simplices.copy())
        plt.plot(np_latlngs[:, 0], np_latlngs[:, 1], 'o')
        plt.plot(new_tri_points[:, 0], new_tri_points[:, 1], 'ro')

        plt.show()

        # print tree.find(".//way[@id='%d']" % self.ways_found[0])
        # ret += ET.tostring(tree.find(".//bounds"))
        # for node_id in self.way_nodes:
        #     ret += ET.tostring(tree.find(".//node[@id='%d']" % node_id))
        # for way_id in self.ways_found:
        #     ret += ET.tostring(tree.find(".//way[@id='%d']" % way_id))
    # Merge a pair of grouped oneways if they are parallel and close to each other
    return

if __name__ == "__main__":
    filename = "../resources/MarylandAvenueNortheast.osm"
    searcher = WaySearcher(filename)

    merge_oneways()
