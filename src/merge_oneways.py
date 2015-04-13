from utilities import WaySearcher

def merge_oneways():
    """
    Merge one way segments that are parallel and close to each other.
    """
    # Find oneways
    # OpenStreetMap oneway: http://wiki.openstreetmap.org/wiki/Key:oneway
    oneways = searcher.find_ways((("highway", None), ("oneway", ("yes", "-1")))).get_ways()

    # Group oneways by street names
    # Merge a pair of grouped oneways if they are parallel and close to each other
    return

if __name__ == "__main__":
    filename = "../resources/MarylandAvenueNortheast.osm"
    searcher = WaySearcher(filename)

    merge_oneway()
