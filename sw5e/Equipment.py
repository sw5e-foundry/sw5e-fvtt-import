import sw5e.Entity, utils.text
import re, json

class Equipment(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.name = utils.text.clean(raw_item, "name")
		self.description = utils.text.clean(raw_item, "description")
		self.cost = utils.text.raw(raw_item, "cost")
		self.weight = utils.text.clean(raw_item, "weight")
		self.equipmentCategoryEnum = utils.text.raw(raw_item, "equipmentCategoryEnum")
		self.equipmentCategory = utils.text.clean(raw_item, "equipmentCategory")
		self.damageNumberOfDice = utils.text.raw(raw_item, "damageNumberOfDice")
		self.damageTypeEnum = utils.text.raw(raw_item, "damageTypeEnum")
		self.damageType = utils.text.clean(raw_item, "damageType")
		self.damageDieModifier = utils.text.raw(raw_item, "damageDieModifier")
		self.weaponClassificationEnum = utils.text.raw(raw_item, "weaponClassificationEnum")
		self.weaponClassification = utils.text.clean(raw_item, "weaponClassification")
		self.armorClassificationEnum = utils.text.raw(raw_item, "armorClassificationEnum")
		self.armorClassification = utils.text.clean(raw_item, "armorClassification")
		self.damageDiceDieTypeEnum = utils.text.raw(raw_item, "damageDiceDieTypeEnum")
		self.damageDieType = utils.text.raw(raw_item, "damageDieType")
		self.properties = utils.text.cleanJson(raw_item, "properties")
		self.propertiesMap = utils.text.cleanJson(raw_item, "propertiesMap")
		self.modes = utils.text.cleanJson(raw_item, "modes")
		self.ac = utils.text.raw(raw_item, "ac")
		self.strengthRequirement = utils.text.raw(raw_item, "strengthRequirement")
		self.stealthDisadvantage = utils.text.raw(raw_item, "stealthDisadvantage")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.uses, self.uses_value, self.recharge = None, None, ''

	def getImg(self, item_type=None, no_img=('Unknown',), default_img='systems/sw5e/packs/Icons/Storage/Crate.webp', plural=False):
		if item_type == None: item_type = self.equipmentCategory

		#TODO: Remove this once there are icons for those categories
		if item_type in no_img: return default_img

		name = self.name
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)

		item_type = re.sub(r'([a-z])([A-Z])', r'\1%20\2', item_type)
		item_type = re.sub(r'\'', r'_', item_type)
		item_type = re.sub(r'And', r'and', item_type)
		item_type = re.sub(r'Or', r'or', item_type)
		if plural: item_type += 's'

		return f'systems/sw5e/packs/Icons/{item_type}/{name}.webp'

	def getWeight(self):
		div = re.match(r'(\d+)/(\d+)', self.weight)
		if div: return int(div.group(1)) / int(div.group(2))
		else: return int(self.weight)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription(importer) } #will call the child's getDescription
		data["data"]["requirements"] = ''
		data["data"]["source"] = self.contentSource
		data["data"]["quantity"] = 1
		data["data"]["weight"] = self.getWeight()
		data["data"]["price"] = self.cost
		data["data"]["attunement"] = 0
		data["data"]["equiped"] = False
		data["data"]["rarity"] = ''
		data["data"]["identified"] = True

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
		return self.equipmentCategory

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
		}
		equipment_type = mapping[raw_item["equipmentCategory"]]
		if not equipment_type:
			print(f'Unexpected item type, {raw_item=}')
			raise ValueError(cls, raw_item["name"], raw_item["equipmentCategory"], raw_item)
		elif equipment_type == 'MEDICAL':
			name = raw_item["name"]
			if re.search('prosthesis', name): equipment_type = 'Equipment'
			else: equipment_type = 'Consumable'

		klass = getattr(getattr(sw5e.equipments, equipment_type.capitalize()), equipment_type.capitalize())
		return klass
