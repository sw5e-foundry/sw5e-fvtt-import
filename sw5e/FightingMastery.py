import sw5e.Feature, utils.text
import re, json

class FightingMastery(sw5e.Feature.BaseFeature):
	def load(self, raw_item):
		super().load(raw_item)

		self.metadata = utils.text.cleanJson(raw_item, "metadata")

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Fighting%20Styles%20and%20Masteries/{name}.webp'
