import sw5e.Feature, utils.text
import re, json

class FightingMastery(sw5e.Feature.CustomizationOption):
	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'modules/sw5e/icons/packs/Fighting%20Styles%20and%20Masteries/{name}.webp'
