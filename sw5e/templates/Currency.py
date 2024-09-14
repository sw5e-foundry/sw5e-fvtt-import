import sw5e.Entity, utils.object

class Currency(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)
		self.currency = self.getCurrency()

	def getCurrency(self):
		return 0

	def getData(self, importer):

		data = super().getData(importer)[0]

		utils.object.setProperty(data, 'system.currency.gp', self.currency, force=True)

		return [data]
