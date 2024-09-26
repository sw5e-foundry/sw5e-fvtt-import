from sw5e.templates import Template
import utils.object

class PhysicalItem(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.quantity': 'quantity',
			'system.weight': 'weight',
			'system.price.value': 'price',
			'system.price.denomination': 'priceDenomination',
			'system.rarity': 'rarity',
		}

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

	def processQuantity(self, importer):
		pass
	def processWeight(self, importer):
		pass
	def processPrice(self, importer):
		pass
	def processPriceDenomination(self, importer):
		pass
	def processRarity(self, importer):
		pass
