from math import radians

class LatLng():
    def __init__(self, lat, lng, node_id=None):
        self.lat = float(lat)
        self.lng = float(lng)
        self.node_id = node_id
        return

    def location(self, radian=True):
        if radian:
            return (radians(self.lat), radians(self.lng))
        else:
            return (self.lat, self.lng)

    def __str__(self):
        return str(self.lat) + "," + str(self.lng)
