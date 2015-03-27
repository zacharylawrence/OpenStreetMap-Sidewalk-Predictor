from imposm.parser import OSMParser
from itertools import islice
import math

# simple class that handles the parsed OSM data.
class HighwayCounter(object):
    coords = {}
    highways = {}
    intersections = set()

    def ways(self, ways):
        for osmid, tags, refs in ways:
            # Only allow 'secondary', 'residential' and 'tertiary' highways to have assumed sidewalks
            valid_highways = set(['secondary', 'residential', 'tertiary', 'residential'])
            if 'highway' in tags and tags['highway'] in valid_highways:
                self.highways[osmid] = refs

    def coords_callback(self, coords):
        for (id, long, lat) in coords:  # Be careful of the order of lat/long -> OSM uses long/lat
            self.coords[id] = (lat, long)

    def calculateIntersections(self):
        seen = set()
        for way, refs in self.highways.items():
            for ref in refs:
                if ref in seen:
                    self.intersections.add(ref)
                seen.add(ref)

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

# instantiate counter and parser and start parsing
counter = HighwayCounter()
p = OSMParser(concurrency=4, ways_callback=counter.ways, coords_callback=counter.coords_callback)
p.parse('map2.osm')
counter.calculateIntersections()

print "Intersections:"
for id in counter.intersections:
	print(counter.coords[id])
print

# Finished parsing, now use the data
for osmid in counter.highways:                  # Way ids
    prev_id = None
    gen = window(counter.highways[osmid], 3)    # Coord ids (in order)
    for ids in gen:
        prev_id, id, next_id = ids

        if id not in counter.intersections:
            prev_lat, prev_long = counter.coords[prev_id]
            lat, long = counter.coords[id]
            next_lat, next_long = counter.coords[next_id]

            in_angle = math.atan2(lat - prev_lat, long - prev_long)
            out_angle = math.atan2(next_lat - lat, next_long - long)

            average_x = (math.sin(in_angle) + math.sin(out_angle)) / 2
            average_y = (math.cos(in_angle) + math.cos(out_angle)) / 2
            average_angle = math.atan2(average_x, average_y)

            perpendicular_angle = math.pi / 2 + average_angle

            # Here we are assuming that things are on a flat plane, not mapped to a globe!
            sidewalk_distance = 5 # In meters - Not currently used, just trial-and-errored 0.00005
            delta_lat = math.sin(perpendicular_angle) * 0.00005
            delta_long = math.cos(perpendicular_angle) * 0.00005

            sidewalk_lat = lat + delta_lat
            sidewalk_long = long + delta_long

            print str(sidewalk_lat) + ',' + str(sidewalk_long)

            sidewalk_lat = lat - delta_lat
            sidewalk_long = long - delta_long

            print str(sidewalk_lat) + ',' + str(sidewalk_long)

    print
