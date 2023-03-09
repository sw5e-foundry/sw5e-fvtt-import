import sw5e.Feature, utils.text
import re, json

class Maneuvers(sw5e.Feature.BaseFeature):
	def load(self, raw_maneuver):
		super().load(raw_maneuver)

		attrs = [ "metadata", "type", "eTag" ]
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_maneuver, attr))

	def getFeatType(self):
		return None, None

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Maneuvers/{name}.webp'

	def getType(self):
		return "maneuver"

	def getAction(self):
		return utils.text.getAction(self.text, self.name, rolled_formula='@scale.superiority.die')

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["maneuverType"] = self.raw_type.lower()

		return [data]

	def getFile(self, importer):
		return f'Maneuver'
