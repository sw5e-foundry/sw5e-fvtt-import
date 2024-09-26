from sw5e.templates import Template
import utils.object

class Currency(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.currency.gp': 'currency',
		}

	def getCurrency(self):
		return 0

	def processCurrency(self, importer):
		pass
