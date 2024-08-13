import sw5e.Feature, utils.text
import re, json

class WeaponFocus(sw5e.Feature.CustomizationOption):
	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'modules/sw5e-module-test/icons/packs/Feats/{name}.webp'
