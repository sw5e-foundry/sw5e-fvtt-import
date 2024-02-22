import sw5e.Equipment, utils.config, utils.text
import re, json

class Consumable(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		self.category, self.subcategory = self.getConsumableType()

		super().process(importer)

		self.uses, self.recharge = utils.text.getUses(self.raw_description, self.name)
		self.activation = utils.text.getActivation(self.raw_description, self.uses, self.recharge)

	def getConsumableType(self):
		mapping = { 
			k: [
				val
				for val in v
				if val["type"] == 'Consumable'
			]
			for k,v in utils.config.equipment_mappings.items()
		}

		# print(f'		{mapping=}');
		for cur in mapping[self.raw_equipmentCategory]:
			# print(f'		{cur=}');
			if function := cur.get("function", None):
				return function(self)
			elif not (pattern := cur.get("pattern", "")) or re.search(pattern.lower(), self.name.lower()):
				return cur.get("category", None), cur.get("subcategory", None)
		else:
			print(f'Unexpected equipment category/name, {self.raw_equipmentCategory=}')
			raise ValueError(self.raw_name, self.raw_equipmentCategory)

	def getEquipmentCategory(self):
		return self.category

	def getEquipmentSubcategory(self):
		return self.subcategory

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.raw_equipmentCategory,
			'no_img': ('Unknown', 'AlcoholicBeverage'),
			'default_img': 'systems/sw5e/packs/Icons/Storage/Canteen.webp',
			# 'plural': False
		}
		if self.subcategory == 'melee': kwargs["item_subtype"] = 'Melee Consumables'
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		text = self.raw_description
		return utils.text.markdownToHtml(text)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["-=consumableType"] = None
		data["system"]["-=ammoType"] = None

		return [data]
