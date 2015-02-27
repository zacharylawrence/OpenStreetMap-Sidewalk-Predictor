from imposm.parser import OSMParser
from itertools import islice
import math

# simple class that handles the parsed OSM data.
class HighwayCounter(object):
    coords = {};
    highways = {};

    def ways(self, ways):
        # callback method for ways
        for osmid, tags, refs in ways:
            # Only allow 'secondary' and 'residential' highways to have assumed sidewalks
            if 'highway' in tags and (tags['highway'] == 'secondary' or tags['highway'] == 'residential'):
                self.highways[osmid] = refs

    def coords_callback(self, coords):
        for (id, long, lat) in coords:  # Be careful of the order of lat/long -> OSM uses long/lat
            self.coords[id] = (lat, long)

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

# Make an angle given in rad between pi and -pi
def normalize_angle(angle):
    angle %= 2 * math.pi
    if (angle > math.pi):
        angle -= 2 * math.pi
    return angle

# instantiate counter and parser and start parsing
counter = HighwayCounter()
p = OSMParser(concurrency=4, ways_callback=counter.ways, coords_callback=counter.coords_callback)
p.parse('map.osm')

# Finished parsing, now use the data
for osmid in counter.highways:                  # Way ids
    prev_id = None
    gen = window(counter.highways[osmid], 3)    # Coord ids (in order)
    for ids in gen:
        prev_id, id, next_id = ids
        prev_lat, prev_long = counter.coords[prev_id]
        lat, long = counter.coords[id]
        next_lat, next_long = counter.coords[next_id]

        in_angle = math.atan2(lat - prev_lat, long - prev_long)
        out_angle = math.atan2(next_lat - lat, next_long - long)

        average_x = math.sin(in_angle) + math.sin(out_angle) / 2
        average_y = math.cos(in_angle) + math.cos(out_angle) / 2
        average_angle = math.atan2(average_x, average_y)

        perpendicular_angle_1 = normalize_angle(math.pi / 2 + average_angle)
        perpendicular_angle_2 = normalize_angle(math.pi / 2 - average_angle)

        print math.degrees(perpendicular_angle_1), math.degrees(perpendicular_angle_2)

        # Here we are assuming that things are on a flat plane, not mapped to a globe!
        deltaY = math.sin(average_angle) * 0.001
        deltaX = math.cos(average_angle) * 0.001

    print


    # for id in counter.highways[osmid]:   # Coord ids (in order)
    #     if prev_id != None:
    #         # print counter.coords[prev_id], " -> ", counter.coords[id]
    #         lat1, long1 = counter.coords[prev_id]
    #         lat2, long2 = counter.coords[id]

    #         theta = math.atan2(lat2 - lat1, long2 - long1)

    #         angle1 = math.pi/2 + theta
    #         angle2 = math.pi/2 - theta

    #         print math.degrees(theta), math.degrees(angle1), math.degrees(angle2)

    #         # Here we are assuming that things are on a flat plane, not mapped to a globe!
    #         sidewalk_distance = 5 # In meters
    #         deltaY = math.sin(angle1) * 0.001
    #         deltaX = math.cos(angle1) * 0.001

    #         print deltaX, deltaY


    #         # if long2 == long1:
    #         #     slope = float("inf")
    #         # else:
    #         #     slope = (lat2 - lat1) / (long2 - long1)

    #         # if slope == 0:
    #         #     perpendicular = float("inf")
    #         # else:
    #         #     perpendicular = -1 / slope

    #         # print slope, perpendicular
    #     prev_id = id
    # print
