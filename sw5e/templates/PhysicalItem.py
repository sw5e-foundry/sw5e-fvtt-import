import sw5e.Entity, utils.object

class PhysicalItem(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)
		self.quantity = self.getQuantity()
		self.weight = self.getWeight()
		self.price = self.getPrice()
		self.price_denomination = self.getPriceDenomination()
		self.rarity = self.getRarity()

	def getQuantity(self):
		return 1
	def getWeight(self):
		raise NotImplementedError
	def getPrice(self):
		raise NotImplementedError
	def getPriceDenomination(self):
		return 'gp'
	def getRarity(self):
		return ''

	def getData(self, importer):
		data = super().getData(importer)[0]

		utils.object.setProperty(data, 'system.quantity', self.quantity, force=True)
		utils.object.setProperty(data, 'system.weight', self.weight, force=True)
		utils.object.setProperty(data, 'system.price.value', self.price, force=True)
		utils.object.setProperty(data, 'system.price.denomination', self.price_denomination, force=True)
		utils.object.setProperty(data, 'system.rarity', self.rarity, force=True)

		return [data]
