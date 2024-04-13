import sw5e.Equipment, utils.text
import re, json

class Loot(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.duration_value, self.duration_unit = None, 'inst'
		self.target_value, self.target_width, self.target_unit, self.target_type = None, None, None, None
		self.range_short, self.range_long, self.range_unit = None, None, None
		self.uses, self.recharge = None, None
		self.action_type, self.damage, self.formula, self.save, self.save_dc = None, None, None, None, None
		self.activation = None

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.equipmentCategory,
			# 'no_img': ('Unknown',),
			'default_img': 'systems/sw5e/packs/Icons/Storage/Crate.webp',
			# 'plural': False
		}
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		text = self.raw_description
		return utils.text.markdownToHtml(text)
