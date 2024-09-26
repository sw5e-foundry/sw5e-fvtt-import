from sw5e.templates import Template
import utils.object

class Identifiable(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.identified': 'identified',
			'system.unidentified.name': 'unidentifiedName',
			'system.unidentified.description': 'unidentifiedDescription',
		}

	def getIdentified(self):
		return True
	def getUnidentifiedName(self):
		return None
	def getUnidentifiedDescription(self):
		return None

	def processIdentified(self, importer):
		pass
	def processUnidentifiedName(self, importer):
		pass
	def processUnidentifiedDescription(self, importer):
		pass
