from imposm.parser import OSMParser

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

# instantiate counter and parser and start parsing
counter = HighwayCounter()
p = OSMParser(concurrency=4, ways_callback=counter.ways, coords_callback=counter.coords_callback)
p.parse('map.osm')

# Finished parsing, now use the data
for osmid in counter.highways:          # Way ids
    for id in counter.highways[osmid]:   # Coord ids
        print counter.coords[id]
    print
