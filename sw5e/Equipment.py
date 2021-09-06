import sw5e.sw5e, utils.text
import re, json

class Equipment(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		# print(self.name)

		self.type = 'loot'

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

	def getImg(self, item_type=None, no_img=('Unknown',), default_img='systems/sw5e/packs/Icons/Storage/Crate.webp', plural=False):
		if item_type == None: item_type = self.equipmentCategory

		#TODO: Remove this once there are icons for those categories
		if item_type in no_img: return default_img

		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		name = re.sub(r'\'', r'_', name)

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
		data = super().getData(importer)
		data["type"] = self.type
		data["img"] = self.getImg() #will call the child's getImg

		data["data"] = {}
		data["data"]["description"] = { "value": self.getDescription() } #will call the child's getDescription
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
			"type": self.action if self.action else None,
			"cost": 1 if self.action else 0,
			"condition": ''
		}

		#TODO: extract duration, target, range, uses, consume, damage and other rolls
		data["data"]["duration"] = {
			"value": None,
			"units": ''
		}
		data["data"]["target"] = {}
		data["data"]["range"] = {}
		data["data"]["uses"] = {
			"value": 0,
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
		data["data"]["armor"] = { "value": 10 }
		data["data"]["hp"] = {
			"value": 0,
			"max": 0,
			"dt": None,
			"conditions": ''
		}
		data["data"]["weaponType"] = ''
		data["data"]["properties"] = {
			"amm": False,
			"aut": False,
			"bur": False,
			"def": False,
			"dex": False,
			"dir": False,
			"drm": False,
			"dgd": False,
			"dis": False,
			"dpt": False,
			"dou": False,
			"fin": False,
			"fix": False,
			"foc": False,
			"hvy": False,
			"hid": False,
			"ken": False,
			"lgt": False,
			"lum": False,
			"mig": False,
			"pic": False,
			"rap": False,
			"rch": False,
			"rel": False,
			"ret": False,
			"shk": False,
			"sil": False,
			"spc": False,
			"str": False,
			"thr": False,
			"two": False,
			"ver": False,
			"vic": False,
			"mgc": False,
			"nodam": False,
			"faulldam": False,
			"fulldam": False
		}
		data["data"]["proficient"] = False

		return [data]

	def matches(self, *args, **kwargs):
		if not super().matches(*args, **kwargs): return False

		if len(args) >= 1:
			new_item = args[0]
			if self.getClass(new_item) != type(self): return False

		return True

	@classmethod
	def getClass(cls, raw_item):
		from sw5e.equipment import Backpack, Consumable, Equipment, Loot, Tool, Weapon
		equipment_type = [
			None, #Unknown
			'Consumable', #Ammunition
			'Consumable', #Explosive
			'Weapon', #Weapon
			'Equipment', #Armor
			'Backpack', #Storage
			None, #None
			'Loot', #Communications
			'Loot', #DataRecordingAndStorage
			'Equipment', #LifeSupport
			'MEDICAL', #Medical
			'Equipment', #WeaponOrArmorAccessory
			'Tool', #Tool
			None, #None
			None, #None
			None, #None
			'Loot', #Utility
			'Tool', #GamingSet
			'Tool', #MusicalInstrument
			None, #None
			'Equipment', #Clothing
			'Tool', #Kit
			'Consumable', #AlcoholicBeverage
			'Consumable', #Spice
		][raw_item["equipmentCategoryEnum"]]
		if equipment_type == None:
			print(f'Unexpected item type, {raw_item=}')
			return cls
		elif equipment_type == 'MEDICAL':
			name = raw_item["name"]
			if re.search('prosthesis', name): equipment_type = 'Equipment'
			else: equipment_type = 'Consumable'

		klass = getattr(getattr(sw5e.equipment, equipment_type.capitalize()), equipment_type.capitalize())
		return klass
