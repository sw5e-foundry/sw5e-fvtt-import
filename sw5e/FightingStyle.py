import sw5e.Feature, utils.text
import re, json

class FightingStyle(sw5e.Feature.BaseFeature):
	def __init__(self, raw_item, old_item, uid, importer):
		self.metadata = utils.text.cleanJson(raw_item, "metadata")

		super().__init__(raw_item, old_item, uid, importer)

	def getType(self):
		return 'fightingstyle'

	def getImg(self):
		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		return f'systems/sw5e/packs/Icons/Fighting%20Styles%20and%20Masteries/{name}.webp'
