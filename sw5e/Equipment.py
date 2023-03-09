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

	def getImg(self, importer=None, item_type=None, no_img=('Unknown',), default_img='systems/sw5e/packs/Icons/Storage/Crate.webp', plural=False):
		if item_type == None: item_type = self.raw_equipmentCategory

		#TODO: Remove this once there are icons for those categories
		if item_type in no_img: return default_img

		item_type = re.sub(r'([a-z])([A-Z])', r'\1%20\2', item_type)
		item_type = re.sub(r'\'', r'_', item_type)
		item_type = re.sub(r'And', r'and', item_type)
		item_type = re.sub(r'Or', r'or', item_type)
		if plural: item_type += 's'

		name = utils.text.slugify(self.raw_name)

		return f'systems/sw5e/packs/Icons/{item_type}/{name}.webp'

	def getWeight(self):
		if type(self.raw_weight) == int: return self.raw_weight
		div = re.match(r'(\d+)/(\d+)', self.raw_weight)
		if div: return int(div.group(1)) / int(div.group(2))

	def getBaseItem(self):
		return re.sub(r'\'|\s+|\([^)]*\)', '', self.raw_name.lower());

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription(importer) } #will call the child's getDescription
		data["data"]["requirements"] = ''
		data["data"]["source"] = self.raw_contentSource
		data["data"]["quantity"] = 1
		data["data"]["weight"] = self.getWeight()
		data["data"]["price"] = self.raw_cost
		data["data"]["attunement"] = 0
		data["data"]["equipped"] = False
		data["data"]["rarity"] = ''
		data["data"]["identified"] = True

		data["data"]["baseItem"] = self.baseItem

		data["data"]["activation"] = {
			"type": self.activation,
			"cost": 1,
			"condition": ''
		} if self.activation != 'none' else {}

		#TODO: extract duration, target, range, consume, damage and other rolls
		data["data"]["duration"] = {
			"value": None,
			"units": ''
		}
		data["data"]["target"] = {}
		data["data"]["range"] = {}
		data["data"]["uses"] = {
			"value": self.uses_value,
			"max": self.uses,
			"per": self.recharge
		}
		data["data"]["consume"] = {}
		data["data"]["ability"] = ''
		data["data"]["actionType"] = ''
		data["data"]["attackBonus"] = 0
		data["data"]["chatFlavor"] = ''
		data["data"]["critical"] = None
		data["data"]["damage"] = {
			"parts": [],
			"versatile": '',
		}
		data["data"]["formula"] = ''
		data["data"]["save"] = {}
		data["data"]["armor"] = {}
		data["data"]["hp"] = {
			"value": 0,
			"max": 0,
			"dt": None,
			"conditions": ''
		}
		data["data"]["weaponType"] = ''
		data["data"]["properties"] = {}
		data["data"]["proficient"] = False

		return [data]

	def getFile(self, importer):
		return self.raw_equipmentCategory

	@classmethod
	def getClass(cls, raw_item):
		from sw5e.equipments import Backpack, Consumable, Equipment, Loot, Tool, Weapon
		mapping = {
			"Unknown": None,
			"Ammunition": 'Consumable',
			"Explosive": 'Consumable',
			"Weapon": 'Weapon',
			"Armor": 'Equipment',
			"Storage": 'Backpack',
			"AdventurePack": 'Backpack',
			"Communications": 'Loot',
			"DataRecordingAndStorage": 'Loot',
			"LifeSupport": 'Equipment',
			"Medical": 'MEDICAL',
			"WeaponOrArmorAccessory": 'Equipment',
			"Tool": 'Tool',
			"Mount": 'Loot',
			"Vehicle": 'Loot',
			"TradeGood": 'Loot',
			"Utility": 'Loot',
			"GamingSet": 'Tool',
			"MusicalInstrument": 'Tool',
			"Droid": 'Loot',
			"Clothing": 'Equipment',
			"Kit": 'Tool',
			"AlcoholicBeverage": 'Consumable',
			"Spice": 'Consumable',
			"Modification": 'Loot'
		}
		equipment_type = None
		if raw_item["name"].lower().find("wristpad") != -1:
			equipment_type = "Equipment"
		elif raw_item["name"].lower().find("focus generator") != -1:
			equipment_type = "Equipment"
		elif raw_item["name"].lower().find("handwrap") != -1:
			equipment_type = "Weapon"
		elif "equipmentCategory" in raw_item and raw_item["equipmentCategory"] in mapping:
			equipment_type = mapping[raw_item["equipmentCategory"]]
		elif "equipment_type" in raw_item:
			equipment_type = raw_item["equipment_type"]
			if equipment_type in mapping: equipment_type = mapping[equipment_type]

		if not equipment_type:
			print(f'Unexpected item type, {raw_item=}')
			raise ValueError(cls, raw_item["name"], raw_item["equipmentCategory"], raw_item)
		elif equipment_type == 'MEDICAL':
			name = raw_item["name"]
			if re.search('prosthesis', name): equipment_type = 'Equipment'
			else: equipment_type = 'Consumable'

		klass = getattr(getattr(sw5e.equipments, equipment_type.capitalize()), equipment_type.capitalize())
		return klass
