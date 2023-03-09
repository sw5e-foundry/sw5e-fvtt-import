import sw5e.Feature, utils.text
import re, json

class FightingStyle(sw5e.Feature.CustomizationOption):
	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Fighting%20Styles%20and%20Masteries/{name}.webp'
