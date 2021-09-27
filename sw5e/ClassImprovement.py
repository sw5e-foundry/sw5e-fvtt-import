import sw5e.Feature, utils.text
import re, json

class ClassImprovement(sw5e.Feature.CustomizationOption):
	def getImg(self):
		name = self.name
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Classes/{name}.webp'
