from sw5e.templates import Template
import utils.object

class ItemDescription(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.description.value': 'description',
			'system.identifier': 'identifier',
			'system.source': 'source',
		}

	def getDescription(self):
		raise NotImplementedError()
	def getIdentifier(self):
		return None
	def getSource(self):
		return { "custom": self.raw_contentSource }

	def processDescription(self, importer):
		pass
	def processIdentifier(self, importer):
		pass
	def processSource(self, importer):
		pass
