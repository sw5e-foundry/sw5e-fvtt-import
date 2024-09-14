import sw5e.Entity, utils.object

class ItemDescription(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)
		self.identifier = self.getIdentifier()
		self.source = self.getSource()

	def process(self, importer):
		self.description = self.getDescription(importer)

	def getDescription(self):
		raise NotImplementedError()

	def getIdentifier(self):
		return None

	def getSource(self):
		return { "custom": self.raw_contentSource }

	def getData(self, importer):
		data = super().getData(importer)[0]

		if self.description: utils.object.setProperty(data, 'system.description.value', self.description, force=True)
		if self.identifier: utils.object.setProperty(data, 'system.identifier', self.identifier, force=True)
		if self.source: utils.object.setProperty(data, 'system.source', self.source, force=True)

		return [data]
