import sw5e.Entity, utils.object

class Identifiable(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)

	def getIdentified(self):
		return True

	def getUnidentifiedName(self):
		return None

	def getUnidentifiedDescription(self):
		return None

	def getData(self, importer):
		data = super().getData(importer)[0]

		if identified := self.getIdentified():
			utils.object.setProperty(data, 'system.identified', identified, force=True)
		if unidentifiedName := self.getUnidentifiedName():
			utils.object.setProperty(data, 'system.unidentified.name', unidentifiedName, force=True)
		if unidentifiedDescription := self.getUnidentifiedDescription():
			utils.object.setProperty(data, 'system.unidentified.description', unidentifiedDescription, force=True)

		return [data]
