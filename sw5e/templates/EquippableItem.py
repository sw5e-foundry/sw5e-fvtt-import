import sw5e.Entity, utils.object

class EquippableItem(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)

		self.attunement = self.getAttunement()
		self.attuned = self.getAttuned()
		self.equipped = self.getEquipped()

	def getAttunement(self):
		return ''
	def getAttuned(self):
		return False
	def getEquipped(self):
		return False

	def getData(self, importer):
		data = super().getData(importer)[0]

		if self.attunement != None: utils.object.setProperty(data, 'system.attunement', self.attunement, force=True)
		if self.attuned != None: utils.object.setProperty(data, 'system.attuned', self.attuned, force=True)
		if self.equipped != None: utils.object.setProperty(data, 'system.equipped', self.equipped, force=True)

		return [data]
