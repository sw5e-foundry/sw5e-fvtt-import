import sw5e.Equipment, utils.config, utils.text
import re, json

class Consumable(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
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

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.raw_equipmentCategory,
			'no_img': ('Unknown', 'AlcoholicBeverage'),
			'default_img': 'modules/sw5e/icons/packs/Storage/Canteen.webp',
			# 'plural': False
		}
		if self.subcategory == 'melee': kwargs["item_subtype"] = 'Melee Consumables'
		return super().getImg(importer=importer, **kwargs)

	def getData(self, importer):
		data = super().getData(importer)[0]

		# TODO: Read these from description
		# utils.object.setProperty(data, 'system.damage.base', 1)
		# utils.object.setProperty(data, 'system.damage.replace', False)
		# utils.object.setProperty(data, 'system.magicalBonus', 0)
		# utils.object.setProperty(data, 'system.uses.autoDestroy', True)

		return [data]

	############################
	#    Template Functions    #
	############################

	# templates.Activities

	# templates.ItemDescription
	def getDescription(self):
		text = self.raw_description
		return utils.text.markdownToHtml(text)

	# templates.Identifiable

	# template.ItemType
	def getCategory(self):
		return self.getConsumableType()[0]

	def getSubcategory(self):
		subcategory = self.getConsumableType()[1]
		if subcategory == 'bolt': return 'crossbowBolt'
		else: return subcategory

	# template.PhysicalItem

	# templates.EquippableItem
