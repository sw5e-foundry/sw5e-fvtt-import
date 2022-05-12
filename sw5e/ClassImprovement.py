import sw5e.Feature, utils.text
import re, json

class ClassImprovement(sw5e.Feature.CustomizationOption):
	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Classes/{name}.webp'
