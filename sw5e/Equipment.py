import sw5e.Entity, utils.text
import re, json

class Equipment(sw5e.Entity.Item):
	def getAttrs(self):
		return super().getAttrs() + [
			"name",
			"description",
			"cost",
			"weight",
			"equipmentCategoryEnum",
			"equipmentCategory",
			"damageNumberOfDice",
			"damageTypeEnum",
			"damageType",
			"damageDieModifier",
			"weaponClassificationEnum",
			"weaponClassification",
			"armorClassificationEnum",
			"armorClassification",
			"damageDiceDieTypeEnum",
			"damageDieType",
			"properties",
			"propertiesMap",
			"modes",
			"ac",
			"strengthRequirement",
			"stealthDisadvantage",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
		]

	def getJsonAttrs(self):
		return super().getJsonAttrs() + [ "propertiesMap" ]

	def process(self, importer):
		super().process(importer)

		self.baseItem = self.getBaseItem()

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_width, self.target_unit, self.target_type = self.getTarget()
		self.range_short, self.range_long, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction()
		self.activation = self.getActivation()

	def getActivation(self):
		return utils.text.getActivation(self.raw_description or '', self.uses, self.recharge)

	def getDuration(self):
		return utils.text.getDuration(self.raw_description or '', self.raw_name)

	def getTarget(self):
		value, unit, ttype = utils.text.getTarget(self.raw_description or '', self.raw_name)
		return value, None, unit, ttype

	def getRange(self):
		short, unit = utils.text.getRange(self.raw_description or '', self.raw_name)
		return short, None, unit

	def getUses(self):
		return utils.text.getUses(self.raw_description or '', self.raw_name)

	def getAction(self):
		return utils.text.getAction((self.raw_description or '').lower(), self.raw_name)

	def getImg(self, importer=None, item_type=None, item_subtype=None, no_img=('Unknown',), default_img='systems/sw5e/packs/Icons/Storage/Crate.webp', plural=False):
		if item_type == None: item_type = self.raw_equipmentCategory

		name = utils.text.slugify(self.raw_name)

		if self.raw_fakeItem: return f'systems/sw5e/packs/Icons/Enhanced%20Items/Generic/{name}.webp'

		#TODO: Remove this once there are icons for those categories
		if item_type in no_img: return default_img

		item_type = re.sub(r'([a-z])([A-Z])', r'\1%20\2', item_type)
		item_type = re.sub(r'\'', r'_', item_type)
		item_type = re.sub(r'And', r'and', item_type)
		item_type = re.sub(r'Or', r'or', item_type)
		if plural: item_type += 's'

		if item_subtype: item_type = f'{item_type}/{item_subtype}'

		return f'systems/sw5e/packs/Icons/{item_type}/{name}.webp'

	def getWeight(self):
		if type(self.raw_weight) == int: return self.raw_weight
		div = re.match(r'(\d+)/(\d+)', self.raw_weight)
		if div: return int(div.group(1)) / int(div.group(2))

	def getBaseItem(self):
		return re.sub(r'\'|\s+|\([^)]*\)', '', self.raw_name.lower());

	def getProperty(self, prop):
		return utils.text.getProperty(prop, self.raw_propertiesMap)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription(importer) } #will call the child's getDescription
		data["system"]["requirements"] = ''
		data["system"]["source"] = self.raw_contentSource
		data["system"]["quantity"] = 1
		data["system"]["weight"] = self.getWeight()
		data["system"]["price"] = {
			"value": self.raw_cost,
			"denomination": "gc"
		}
		data["system"]["attunement"] = 0
		data["system"]["equipped"] = False
		data["system"]["rarity"] = ''
		data["system"]["identified"] = True

		data["system"]["baseItem"] = self.baseItem

		if self.activation: data["system"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation != 'none' else None
		}
		if self.duration_value or self.duration_unit: data["system"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		if self.target_value or self.target_width or self.target_unit or self.target_type: data["system"]["target"] = {
			"value": self.target_value,
			"width": self.target_width,
			"units": self.target_unit,
			"type": self.target_type
		}
		if self.range_short or self.range_long or self.range_unit: data["system"]["range"] = {
			"value": self.range_short,
			"long": self.range_long,
			"units": self.range_unit
		}
		if self.uses or self.recharge: data["system"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}
		if self.action_type: data["system"]["actionType"] = self.action_type

		if self.damage: data["system"]["damage"] = {
			"parts": self.damage["parts"],
			"versatile": self.damage["versatile"]
		}
		if self.formula: data["system"]["formula"] = self.formula
		if self.save: data["system"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": 'flat' if self.save_dc else 'none'
		}

		return [data]

	def getFile(self, importer):
		return self.raw_equipmentCategory

	@classmethod
	def getClass(cls, raw_item):
		from sw5e.equipments import Backpack, Consumable, Equipment, Loot, Tool, Weapon

		name = raw_item["name"].lower()
		mapping = utils.config.equipment_mappings
		equipment_mapping = None
		equipment_type = None

		if "equipmentCategory" in raw_item and raw_item["equipmentCategory"] in mapping:
			equipment_mapping = mapping[raw_item["equipmentCategory"]]

		if not equipment_mapping:
			print(f'Unexpected item type, {raw_item=}')
			raise ValueError(cls, raw_item["name"], raw_item["equipmentCategory"], raw_item)
		for cur in equipment_mapping:
			# print(f'		{cur=}');
			# print(f'		{raw_item=}');
			pattern = cur.get("pattern", "")
			if re.search(pattern, name):
				equipment_type = cur["type"]
				break
		else:
			print(f'Unexpected item type, {raw_item=}')
			raise ValueError(cls, raw_item["name"], raw_item["equipmentCategory"], raw_item, equipment_mapping)

		klass = getattr(getattr(sw5e.equipments, equipment_type.capitalize()), equipment_type.capitalize())
		return klass
