import sw5e.Equipment, utils.text
import re, json

class Loot(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.uses, self.recharge = utils.text.getUses(self.description, self.name)
		self.activation = utils.text.getActivation(self.description, self.uses, self.recharge)

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.equipmentCategory,
			# 'no_img': ('Unknown',),
			'default_img': 'systems/sw5e/packs/Icons/Storage/Crate.webp',
			# 'plural': False
		}
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		text = self.description
		return utils.text.markdownToHtml(text)
