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

		self.uses, self.uses_value, self.recharge = None, None, None
		self.baseItem = self.getBaseItem()

	def getImg(self, importer=None, item_type=None, item_subtype=None, no_img=('Unknown',), default_img='systems/sw5e/packs/Icons/Storage/Crate.webp', plural=False):
		if item_type == None: item_type = self.raw_equipmentCategory

		#TODO: Remove this once there are icons for those categories
		if item_type in no_img: return default_img

		item_type = re.sub(r'([a-z])([A-Z])', r'\1%20\2', item_type)
		item_type = re.sub(r'\'', r'_', item_type)
		item_type = re.sub(r'And', r'and', item_type)
		item_type = re.sub(r'Or', r'or', item_type)
		if plural: item_type += 's'

		if item_subtype: item_type = f'{item_type}/{item_subtype}'

		name = utils.text.slugify(self.raw_name)

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

		data["system"]["activation"] = {
			"type": self.activation,
			"cost": 1,
			"condition": ''
		} if self.activation != 'none' else {}

		#TODO: extract duration, target, range, consume, damage and other rolls
		data["system"]["duration"] = {
			"value": None,
			"units": ''
		}
		data["system"]["target"] = {}
		data["system"]["range"] = {}
		data["system"]["uses"] = {
			"value": self.uses_value,
			"max": self.uses,
			"per": self.recharge
		}
		data["system"]["consume"] = {}
		data["system"]["ability"] = ''
		data["system"]["actionType"] = ''
		data["system"]["attackBonus"] = 0
		data["system"]["chatFlavor"] = ''
		data["system"]["critical"] = None
		data["system"]["damage"] = {
			"parts": [],
			"versatile": '',
		}
		data["system"]["formula"] = ''
		data["system"]["save"] = {}
		data["system"]["armor"] = {}
		data["system"]["hp"] = {
			"value": 0,
			"max": 0,
			"dt": None,
			"conditions": ''
		}
		data["system"]["weaponType"] = ''
		data["system"]["properties"] = {}
		data["system"]["proficient"] = None

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
