import sw5e.Feature, utils.text
import re, json

class Feat(sw5e.Feature.BaseFeature):
	def __init__(self, raw_item, old_item, uid, importer):
		self.attributesIncreased = utils.text.cleanJson(raw_item, "attributesIncreased")

		super().__init__(raw_item, old_item, uid, importer)

	def getType(self):
		return 'feat'

	def getImg(self):
		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		return f'systems/sw5e/packs/Icons/Feats/{name}.webp'
