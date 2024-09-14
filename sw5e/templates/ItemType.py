import sw5e.Entity, utils.object

class ItemType(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)
		self.category = self.getCategory()
		self.subcategory = self.getSubcategory()
		self.base_item = self.getBaseItem()

	def getCategory(self):
		raise NotImplementedError()
	def getSubcategory(self):
		raise NotImplementedError()
	def getBaseItem(self):
		raise NotImplementedError()

	def getData(self, importer):
		data = super().getData(importer)[0]

		if self.category: utils.object.setProperty(data, 'system.type.value', self.category, force=True)
		if self.subcategory: utils.object.setProperty(data, 'system.type.subtype', self.subcategory, force=True)
		if self.base_item: utils.object.setProperty(data, 'system.type.baseItem', self.base_item, force=True)

		return [data]
