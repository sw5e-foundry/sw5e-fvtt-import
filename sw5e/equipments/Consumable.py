import sw5e.Equipment, utils.text
import re, json

class Consumable(sw5e.Equipment.Equipment):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.type = 'consumable'

		self.uses, self.recharge = utils.text.getUses(self.description, self.name)
		self.action = utils.text.getActivation(self.description, self.uses, self.recharge)

		if self.name == 'Power cell' or (self.description or '').startswith(f'A {self.name.lower()} is a specializard power cell'):
			self.action = 'bonus'
			self.uses_value = 480
			self.uses = 480
			self.recharge = 'charges'

	def getImg(self):
		kwargs = {
			# 'item_type': self.equipmentCategory,
			'no_img': ('Unknown', 'AlcoholicBeverage'),
			'default_img': 'systems/sw5e/packs/Icons/Utility/Canteen.webp',
			# 'plural': False
		}
		return super().getImg(**kwargs)

	def getDescription(self, importer):
		text = self.description
		return utils.text.markdownToHtml(text)
