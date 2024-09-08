import sw5e.Feature, utils.text
import re, json

class LightsaberForm(sw5e.Feature.CustomizationOption):
	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'modules/sw5e/icons/packs/Lightsaber%20Forms/{name}.webp'
