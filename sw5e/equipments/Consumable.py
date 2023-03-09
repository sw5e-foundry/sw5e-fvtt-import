import sw5e.Equipment, utils.text
import re, json

class Consumable(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.uses, self.recharge = utils.text.getUses(self.raw_description, self.name)
		self.activation = utils.text.getActivation(self.raw_description, self.uses, self.recharge)
		self.consumable_type, self.ammo_type = self.getConsumableType()

	def getConsumableType(self):
		consumable_type, ammo_type = None, None

		mapping = {
			"Ammunition": 'ammo',
			"Explosive": 'explosive',
			"AlcoholicBeverage": 'adrenal',
			"Spice": 'adrenal',
			"Medical": 'medpac',
		}
		if self.raw_equipmentCategory in mapping:
			consumable_type = mapping[self.raw_equipmentCategory]
		else:
			raise ValueError(self.name, self.raw_equipmentCategory)

		if consumable_type == 'ammo':
			ammo_types = utils.config.ammo_types
			name = self.name.lower()
			for ammo in ammo_types:
				amn = ammo["name"].lower()
				if name.find(amn) != -1:
					ammo_type = ammo["id"]
					break
			if not ammo_type:
				desc = (self.raw_description or '').lower()
				for ammo in ammo_types:
					amn = ammo["name"].lower()
					if desc.find(amn) != -1:
						ammo_type = ammo["id"]
						break

		return consumable_type, ammo_type

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.raw_equipmentCategory,
			'no_img': ('Unknown', 'AlcoholicBeverage'),
			'default_img': 'systems/sw5e/packs/Icons/Storage/Canteen.webp',
			# 'plural': False
		}
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		text = self.raw_description
		return utils.text.markdownToHtml(text)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["consumableType"] = self.consumable_type
		if self.ammo_type: data["data"]["ammoType"] = self.ammo_type

		return [data]
