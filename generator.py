class Generator(object):
	output = []
	nodes = []  # (id, long, lat)
	ways = {}  # id -> ([node_ref], [(tag_key, tag_value)])
	bounds = None  # minlat, minlon, maxlat, maxlon
	id_gen = None  # Used to generate the next valid id (increments from 1)

	def __init__(self):
		self.id_gen = self.create_id()

	def create_id(self):
		count = 1

		while True:
			yield count
			count += 1

	def add_coord(self, long, lat):
		id = self.id_gen.next()

		if self.bounds is None:
			self.bounds = (lat, long, lat, long)
		else:
			self.bounds[0] = Math.min(self.bounds[0], lat)
			self.bounds[1] = Math.min(self.bounds[1], long)
			self.bounds[2] = Math.max(self.bounds[2], lat)
			self.bounds[3] = Math.max(self.bounds[3]. long)

		self.nodes.append((id, long, lat))

		return id

	def add_way(self, tags):
		id = self.id_gen.next()

		self.ways[id] = ([], tags)

		return id

	def add_way_reference(self, way_id, node_id):
		self.ways[way_id][0].append(node_id)

	def generate_header(self):
		self.output.append('<?xml version="1.0" encoding="UTF-8"?>')
		self.output.append('<osm version="0.6">')
		self.output.append('<bounds minlat="' + str(self.bounds[0]) + \
			'" minlon="' + str(self.bounds[1]) + \
			'" maxlat="' + str(self.bounds[2]) + \
			'" maxlon="' + str(self.bounds[3]) + '"/>')

	def generate_footer(self):
		self.output.append('</osm>')

	def generate_nodes(self):
		for (id, long, lat) in self.nodes:
			self.output.append(' <node id="' + str(id) + \
				'" visible="true" user="test" lat="' + str(lat) + \
				'" lon="' + str(long) +'"/>')

	def generate_ways(self):
		for id in self.ways:
			(node_ids, tags) = self.ways[id]

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
		self.generate_footer()

		return '\n'.join(self.output)
