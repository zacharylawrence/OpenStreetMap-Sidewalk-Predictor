class Generator(object):
	output = list()
	nodes = list()
	ways = list()
	bounds = None # minlat, minlon, maxlat, maxlon

	def add_coord(self, id, long, lat):
		if self.bounds is None:
			self.bounds = (lat, long, lat, long)
		else:
			self.bounds[0] = Math.min(self.bounds[0], lat)
			self.bounds[1] = Math.min(self.bounds[1], long)
			self.bounds[2] = Math.max(self.bounds[2], lat)
			self.bounds[3] = Math.max(self.bounds[3]. long)

		self.nodes.append((id, long, lat))

	def add_way(self, id, node_ids, tags):
		self.ways.append((id, node_ids, tags))

	def generate_header(self):
		self.output.append('<?xml version="1.0" encoding="UTF-8"?>')
		self.output.append('<osm version="0.6">')
		self.output.append('<bounds minlat="' + str(self.bounds[0]) + \
			'" minlon="' + str(self.bounds[1]) + \
			'" maxlat="' + str(self.bounds[2]) + \
			'" maxlon="' + str(self.bounds[3]) + '"/>')

	def generate_nodes(self):
		for (id, long, lat) in self.nodes:
			self.output.append(' <node id="' + str(id) + \
				'" visible="true" user="test" lat="' + str(lat) + \
				'" lon="' + str(long) +'"/>')

	def generate_ways(self):
		for (id, node_ids, tags) in self.ways:
			self.output.append(' <way id="' + str(id) + \
				'" visible="true" user="test">')

			for node_id in node_ids:
				self.output.append('  <nd ref="' + str(node_id) + '"/>')

			for (key, value) in tags:
				self.output.append('  <tag k="' + str(key) + \
					'" v="' + str(value) + '"/>')

			self.output.append(' </way>')


	def generate(self):
		self.generate_header()
		self.generate_nodes()
		self.generate_ways()
		return '\n'.join(self.output)
