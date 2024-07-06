import sw5e.Feature, utils.text
import re, json

class Maneuvers(sw5e.Feature.BaseFeature):
	def getAttrs(self):
		return super().getAttrs() + [ "metadata", "type", "eTag" ]

	def getType(self):
		return "maneuver"

	def getFeatType(self):
		return None, None

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Maneuvers/{name}.webp'

	def getAction(self):
		return utils.text.getAction(self.raw_text, self.name, rolled_formula='@scale.superiority.die')

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["type"] = { "value": self.raw_type.lower() }

		return [data]

	def getFile(self, importer):
		return f'Maneuver'
