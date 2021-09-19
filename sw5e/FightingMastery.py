import sw5e.Feature, utils.text
import re, json

class FightingMastery(sw5e.Feature.BaseFeature):
	def load(self, raw_item):
		super().load(raw_item)

		self.metadata = utils.text.cleanJson(raw_item, "metadata")

	def process(self, old_item, importer):
		super().process(old_item, importer)

	def getImg(self):
		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		return f'systems/sw5e/packs/Icons/Fighting%20Styles%20and%20Masteries/{name}.webp'
