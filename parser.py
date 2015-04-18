import math
import logging as log
from itertools import islice

from imposm.parser import OSMParser

from generator import Generator

# simple class that handles the parsed OSM data.
class HighwayCounter(object):
    coords = {}  # node_id -> (lat, long)
    highways = {}  # way_id -> [node_ref]
    intersections = {}  # duplicate_node_ref -> [adjacent_node_ref]

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
            id = refs[0]
            if id in seen:
                if (id not in self.intersections):
                    self.intersections[id] = []
                self.intersections[id].append(refs[1])
            seen.add(refs[0])

            gen = window(refs, 3)
            for ids in gen:
                prev_id, id, next_id = ids

                if id in seen:
                    if (id not in self.intersections):
                        self.intersections[id] = []
                    self.intersections[id].append(prev_id)
                    self.intersections[id].append(next_id)

                seen.add(id)

            # Handle last element
            id = refs[-1]
            if id in seen:
                if (id not in self.intersections):
                    self.intersections[id] = []
                self.intersections[id].append(refs[-2])
            seen.add(id)

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

def add_non_intersection(prev_id, id, next_id):
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

    perpendicular_angle = math.pi / 2 + average_angle

    # Here we are assuming that things are on a flat plane, not mapped to a globe!
    sidewalk_distance = 5 # In meters - Not currently used, just trial-and-errored 0.00005
    delta_lat = math.sin(perpendicular_angle) * 0.00005
    delta_long = math.cos(perpendicular_angle) * 0.00005

    sidewalk_lat1 = lat + delta_lat
    sidewalk_long1 = long + delta_long

    sidewalk_lat2 = lat - delta_lat
    sidewalk_long2 = long - delta_long

    return (sidewalk_long1, sidewalk_lat1, sidewalk_long2, sidewalk_lat2)

# instantiate counter and parser and start parsing
if __name__ == "__main__":
    # log.basicConfig(format="", level=log.DEBUG)

    counter = HighwayCounter()
    output = Generator()
    p = OSMParser(concurrency=4, ways_callback=counter.ways, coords_callback=counter.coords_callback)
    p.parse('map2.osm')
    counter.calculateIntersections()

    # Finished parsing, now use the data
    # log.debug("Intersections:")
    for id in counter.intersections:
        log.debug(str(counter.coords[id][0]) + ',' + str(counter.coords[id][1]))
        for adjacent_node_ref in counter.intersections[id]:
            log.debug(str(counter.coords[adjacent_node_ref][0]) + ',' + str(counter.coords[adjacent_node_ref][1]))
        log.debug('\n')
    log.debug('\n')

    log.debug("Sidewalks:")
    for osmid in counter.highways:  # Way ids
        way1 = output.add_way([('highway', 'footway')])
        way2 = output.add_way([('highway', 'footway')])

        # First Coord id Case:
        if len(counter.highways[osmid]) > 1:
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

        # Last Coord id Case:
        if len(counter.highways[osmid]) > 1:
            id = counter.highways[osmid][-1]
            prev_id = counter.highways[osmid][-2]

            if id not in counter.intersections:
                (sidewalk_long1, sidewalk_lat1, sidewalk_long2, sidewalk_lat2) = add_non_intersection(prev_id, id, None)
                output.add_way_reference(way1, output.add_coord(sidewalk_long1, sidewalk_lat1))
                output.add_way_reference(way2, output.add_coord(sidewalk_long2, sidewalk_lat2))


        log.debug(str(sidewalk_lat1) + ',' + str(sidewalk_long1))
        log.debug(str(sidewalk_lat2) + ',' + str(sidewalk_long2))
        log.debug('\n')

    print output.generate()
