from utilities import WaySearcher




if __name__ == "__main__":
    filename = "../resources/MarylandAvenueNortheast.osm"
    searcher = WaySearcher(filename)
    print searcher.find_ways((("highway", None), ("oneway", "yes"))).get_ways()
