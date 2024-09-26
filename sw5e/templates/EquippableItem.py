from sw5e.templates import Template
import utils.object

class EquippableItem(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.attunement': 'attunement',
			'system.attuned': 'attuned',
			'system.equipped': 'equipped',
		}

	def getAttunement(self):
		return None
	def getAttuned(self):
		return None
	def getEquipped(self):
		return None

	def processAttunement(self, importer):
		pass
	def processAttuned(self, importer):
		pass
	def processEquipped(self, importer):
		pass
