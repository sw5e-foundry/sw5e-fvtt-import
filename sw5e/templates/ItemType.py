from sw5e.templates import Template
import utils.object

class ItemType(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.type.value': 'category',
			'system.type.subtype': 'subcategory',
			'system.type.baseItem': 'baseItemName',
		}

	def getCategory(self):
		raise NotImplementedError()
	def getSubcategory(self):
		raise NotImplementedError()
	def getBaseItemName(self):
		raise NotImplementedError()

	def processCategory(self, importer):
		pass
	def processSubcategory(self, importer):
		pass
	def processBaseItemName(self, importer):
		pass
