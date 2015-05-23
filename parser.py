import math
import logging as log
from itertools import islice

from imposm.parser import OSMParser

from generator import Generator
from math import radians

# simple class that handles the parsed OSM data.
class HighwayCounter(object):
    coords = {}  # node_id -> (lat, long)
    highways = {}  # way_id -> [node_ref]
    intersections = set()
    adjacent = {}  # node_ref -> [adjacent_node_ref]

    def ways(self, ways):
        for osmid, tags, refs in ways:
            # Only allow the following highways to have assumed sidewalks
            valid_highways = set(['primary', 'secondary', 'tertiary', 'residential'])
            if 'highway' in tags and tags['highway'] in valid_highways:
                self.highways[osmid] = refs

    def coords_callback(self, coords):
        for (id, long, lat) in coords:  # Be careful of the order of lat/long -> OSM uses long/lat
            self.coords[id] = (lat, long)

    def calculateIntersections(self):
        seen = set()
        for refs in self.highways.values():
            # Handle first element
            if (len(refs) >= 1):  # We must contain at least 1 element to have a first
                id = refs[0]
                if id in seen:
                    self.intersections.add(id)
                seen.add(refs[0])

                if (id not in self.adjacent):
                    self.adjacent[id] = []
                self.adjacent[id].append(refs[1])

            # Handle middle elements
            gen = window(refs, 3)
            for ids in gen:
                prev_id, id, next_id = ids

                if id in seen:
                    self.intersections.add(id)
                seen.add(id)

                if (id not in self.adjacent):
                    self.adjacent[id] = []
                self.adjacent[id].append(prev_id)
                self.adjacent[id].append(next_id)


            # Handle last element
            if (len(refs) >= 2):  # We must contain at least 2 elements to have a last that isn't a first
                id = refs[-1]
                if id in seen:
                    self.intersections.add(id)
                seen.add(id)

                if (id not in self.adjacent):
                    self.adjacent[id] = []
                self.adjacent[id].append(refs[-2])

        # Sort each set of adjacent intersection coords by angle from intersection coord (from: -pi to pi)
        # Note: We only sort the adjacent array for intersections
        for id in self.adjacent:
        # for id in self.intersections:
            self.adjacent[id].sort(key=lambda c:math.atan2(self.coords[c][0]-self.coords[id][0], self.coords[c][1]-self.coords[id][1]))

# Helper sliding window iterater method
# See: http://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python
def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

# TODO: Remove this
# Make an angle given in rad between pi and -pi
# def normalize_angle(angle):
#     angle %= 2 * math.pi
#     if (angle > math.pi):
#         angle -= 2 * math.pi
#     return angle

def get_perpendicular_angle(prev_id, id, next_id):
    lat, long = counter.coords[id]

    if prev_id is not None:
        prev_lat, prev_long = counter.coords[prev_id]
        in_angle = math.atan2(lat - prev_lat, long - prev_long)
        average_angle = in_angle

    if next_id is not None:
        next_lat, next_long = counter.coords[next_id]
        out_angle = math.atan2(next_lat - lat, next_long - long)
        average_angle = out_angle

    if prev_id is not None and next_id is not None:
        average_x = (math.sin(in_angle) + math.sin(out_angle)) / 2
        average_y = (math.cos(in_angle) + math.cos(out_angle)) / 2
        average_angle = math.atan2(average_x, average_y)

    return math.pi / 2 + average_angle


def add_non_intersection(prev_id, id, next_id):
    lat, long = counter.coords[id]
    perpendicular_angle = get_perpendicular_angle(prev_id, id, next_id)

    # Here we are assuming that things are on a flat plane, not mapped to a globe!
    sidewalk_distance = 5 # In meters - Not currently used, just trial-and-errored 0.00005
    delta_lat = math.sin(perpendicular_angle) * 0.00005
    delta_long = math.cos(perpendicular_angle) * 0.00005

    sidewalk_lat1 = lat + delta_lat
    sidewalk_long1 = long + delta_long

    sidewalk_lat2 = lat - delta_lat
    sidewalk_long2 = long - delta_long

    return (sidewalk_long1, sidewalk_lat1, sidewalk_long2, sidewalk_lat2)


def add_intersection(prev_id, intersection_id, adjacent_id):
    lat, long = counter.coords[id]
    perpendicular_angle = get_perpendicular_angle(prev_id, intersection_id, adjacent_id)

    # Here we are assuming that things are on a flat plane, not mapped to a globe!
    sidewalk_distance = 5 # In meters - Not currently used, just trial-and-errored 0.00005
    delta_lat = math.sin(perpendicular_angle) * 0.00010
    delta_long = math.cos(perpendicular_angle) * 0.00010

    sidewalk_lat = lat + delta_lat
    sidewalk_long = long + delta_long

    return (sidewalk_long, sidewalk_lat)  #Todo: KH. Change this output to a LatLng object


def get_adjacent_id(prev_id, intersection_id):
    adjacent_list = counter.adjacent[intersection_id]
    intersection_id_index = adjacent_list.index(prev_id)
    adjacent_id1 = adjacent_list[(intersection_id_index + 1) % len(adjacent_list)]
    adjacent_id2 = adjacent_list[(intersection_id_index - 1) % len(adjacent_list)]

    return (adjacent_id1, adjacent_id2)

# instantiate counter and parser and start parsing
if __name__ == "__main__":
    log.basicConfig(format="", level=log.DEBUG)

    counter = HighwayCounter()
    output = Generator()
    p = OSMParser(concurrency=4, ways_callback=counter.ways, coords_callback=counter.coords_callback)
    p.parse('SmallMap_02.osm')
    counter.calculateIntersections()

    # Finished parsing, now use the data
    sidewalk_nodes = {}  # set{two adjacent nodes} -> newly created sidewalk node


    # Todo: KH: Instead of tuples, we should create and use a LatLng class like what I did in the merge-oneway branch.
    log.debug("Intersections & Adjacent Coords:")
    for id in counter.intersections:
        log.debug(str(counter.coords[id][0]) + ',' + str(counter.coords[id][1]))
        for adjacent_node_ref in counter.adjacent[id]:
            adj = counter.coords[adjacent_node_ref]
            log.debug(str(adj[0]) + ',' + str(adj[1]))
        log.debug('\n')
    log.debug('\n')

    # Go through each streets (highways) and create sidewalks on the both sides
    log.debug("Sidewalks:")
    for osmid in counter.highways:  # Way ids
        way1 = output.add_way([('highway', 'footway')])
        way2 = output.add_way([('highway', 'footway')])

        # First Coord id Case:
        if len(counter.highways[osmid]) > 1:  # TODO: should this be '>= 1' ?
            id = counter.highways[osmid][0]
            next_id = counter.highways[osmid][1]

            if id not in counter.intersections:
                (sidewalk_long1, sidewalk_lat1, sidewalk_long2, sidewalk_lat2) = add_non_intersection(None, id, next_id)
                output.add_way_reference(way1, output.add_coord(sidewalk_long1, sidewalk_lat1))
                output.add_way_reference(way2, output.add_coord(sidewalk_long2, sidewalk_lat2))

        # Middle Case (Size 3 sliding window of Coord ids (in order)):
        gen = window(counter.highways[osmid], 3)
        for ids in gen:
            prev_id, id, next_id = ids

            if id not in counter.intersections:
                (sidewalk_long1, sidewalk_lat1, sidewalk_long2, sidewalk_lat2) = add_non_intersection(prev_id, id, next_id)
                output.add_way_reference(way1, output.add_coord(sidewalk_long1, sidewalk_lat1))
                output.add_way_reference(way2, output.add_coord(sidewalk_long2, sidewalk_lat2))
            # else:
            #     (adjacent_id1, adjacent_id2) = get_adjacent_id(prev_id, id)
            #     (sidewalk_long1, sidewalk_lat1) = add_intersection(prev_id, id, adjacent_id1)
            #     (sidewalk_long2, sidewalk_lat2) = add_intersection(prev_id, id, adjacent_id2)

            #     key1 = (id, adjacent_id1) if id < adjacent_id1 else (adjacent_id1, id)
            #     key2 = (id, adjacent_id2) if id < adjacent_id2 else (adjacent_id2, id)

            #     if (key1 in sidewalk_nodes):
            #         output.add_way_reference(way1, sidewalk_nodes[key1])
            #     else:
            #         # Add these the the sidewalk_nodes map
            #         sidewalk_node1 = output.add_coord(sidewalk_long1, sidewalk_lat1)
            #         sidewalk_nodes[key1] = sidewalk_node1
            #         # Add these to the generator
            #         output.add_way_reference(way1, output.add_coord(sidewalk_long1, sidewalk_lat1))

            #     if (key2 in sidewalk_nodes):
            #         output.add_way_reference(way2, sidewalk_nodes[key2])
            #     else:
            #         # Add these the the sidewalk_nodes map
            #         sidewalk_node2 = output.add_coord(sidewalk_long2, sidewalk_lat2)
            #         sidewalk_nodes[key2] = sidewalk_node2
            #         # Add these to the generator
            #         output.add_way_reference(way2, output.add_coord(sidewalk_long2, sidewalk_lat2))

        # Last Coord id Case:
        if len(counter.highways[osmid]) > 1:  # TODO: should this be '>= 2' ?
            id = counter.highways[osmid][-1]
            prev_id = counter.highways[osmid][-2]

            if id not in counter.intersections:
                (sidewalk_long1, sidewalk_lat1, sidewalk_long2, sidewalk_lat2) = add_non_intersection(prev_id, id, None)
                output.add_way_reference(way1, output.add_coord(sidewalk_long1, sidewalk_lat1))
                output.add_way_reference(way2, output.add_coord(sidewalk_long2, sidewalk_lat2))

        if id in counter.intersections:
            (adjacent_id1, adjacent_id2) = get_adjacent_id(prev_id, id)
            (sidewalk_long1, sidewalk_lat1) = add_intersection(prev_id, id, adjacent_id1)
            (sidewalk_long2, sidewalk_lat2) = add_intersection(prev_id, id, adjacent_id2)

            # log.debug(str(counter.coords[adjacent_id1][0]) + ',' + str(counter.coords[adjacent_id1][1]))
            # log.debug(str(counter.coords[adjacent_id2][0]) + ',' + str(counter.coords[adjacent_id2][1]))

            key1 = (id, adjacent_id1) if id < adjacent_id1 else (adjacent_id1, id)
            key2 = (id, adjacent_id2) if id < adjacent_id2 else (adjacent_id2, id)

            if (key1 in sidewalk_nodes):
                output.add_way_reference(way1, sidewalk_nodes[key1])
            else:
                # Add these the the sidewalk_nodes map
                sidewalk_node1 = output.add_coord(sidewalk_long1, sidewalk_lat1)
                sidewalk_nodes[key1] = sidewalk_node1
                # Add these to the generator
                output.add_way_reference(way1, output.add_coord(sidewalk_long1, sidewalk_lat1))

            if (key2 in sidewalk_nodes):
                output.add_way_reference(way2, sidewalk_nodes[key2])
            else:
                # Add these the the sidewalk_nodes map
                sidewalk_node2 = output.add_coord(sidewalk_long2, sidewalk_lat2)
                sidewalk_nodes[key2] = sidewalk_node2
                # Add these to the generator
                output.add_way_reference(way2, output.add_coord(sidewalk_long2, sidewalk_lat2))


            # log.debug(str(sidewalk_lat1) + ',' + str(sidewalk_long1))
            # log.debug(str(sidewalk_lat2) + ',' + str(sidewalk_long2))
        # log.debug('\n')

    print output.generate()
