import sw5e.Feature, utils.text
import re, json

class MulticlassImprovement(sw5e.Feature.CustomizationOption):
	def getImg(self):
		name = self.name
		return f'systems/sw5e/packs/Icons/Classes/{name}.webp'
