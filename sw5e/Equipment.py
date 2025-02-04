import sw5e.Entity, sw5e.templates, utils.text
import re, json

class Equipment(
	sw5e.Entity.Item,
	sw5e.templates.Activities,
	sw5e.templates.ItemDescription,
	sw5e.templates.ItemType,
	sw5e.templates.Identifiable,
	sw5e.templates.PhysicalItem,
	sw5e.templates.EquippableItem,
):
	_equipment_types_registry = {}

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._equipment_types_registry[cls.__name__.lower()] = cls

	def __new__(cls, raw_item, importer=None, importer_version=None):
		equipment_type = cls.getEquipmentType(raw_item)

		subclass = cls._equipment_types_registry[equipment_type.lower()]
		return object.__new__(subclass)

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

	def load(self, raw_item):
		super().load(raw_item)
		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_width, self.target_unit, self.target_type = self.getTarget()
		self.range_short, self.range_long, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction()
		self.activation = self.getActivation()
		self.p_properties = self.getProperties()

	def process(self, importer):
		super().process(importer)

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

	def getImg(self, importer=None, item_type=None, item_subtype=None, no_img=('Unknown',), default_img='modules/sw5e/icons/packs/Storage/Crate.webp', plural=False):
		if item_type == None: item_type = self.raw_equipmentCategory

		name = utils.text.slugify(self.raw_name)

		if self.raw_fakeItem: return f'modules/sw5e/icons/packs/Enhanced%20Items/Generic/{name}.webp'

		#TODO: Remove this once there are icons for those categories
		if item_type in no_img: return default_img

		item_type = re.sub(r'([a-z])([A-Z])', r'\1%20\2', item_type)
		item_type = re.sub(r'\'', r'_', item_type)
		item_type = re.sub(r'And', r'and', item_type)
		item_type = re.sub(r'Or', r'or', item_type)
		if plural: item_type += 's'

		if item_subtype: item_type = f'{item_type}/{item_subtype}'

		return f'modules/sw5e/icons/packs/{item_type}/{name}.webp'

	def getProperty(self, prop):
		return utils.text.getProperty(prop, self.raw_propertiesMap)

	def getPropertiesList(self):
		return None

	def getProperties(self):
		return None

	def getData(self, importer):
		data = super().getData(importer)[0]

		# templates.Activities
		# templates.ItemDescription
		# templates.Identifiable
		# templates.ItemType
		# templates.PhysicalItem
		# templates.EquippableItem
		## templates.Mountable -- NotImplemented

		if self.p_properties:
			properties = { key: value for key, value in self.p_properties.items() if value }
			utils.object.setProperty(data, 'flags.sw5e.properties', properties, force=True)
			utils.object.setProperty(data, 'system.properties', list(properties.keys()), force=True)

		return [data]

	def getFile(self, importer):
		return self.raw_equipmentCategory

	@classmethod
	def getEquipmentType(cls, raw_item):
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
			pattern = cur.get("pattern", "")
			if re.search(pattern, name):
				equipment_type = cur["type"]
				break
		else:
			print(f'Unexpected item type, {raw_item=}')
			raise ValueError(cls, raw_item["name"], raw_item["equipmentCategory"], raw_item, equipment_mapping)

		return equipment_type

	############################
	#    Template Functions    #
	############################

	# templates.Activities
	def getActivitiesData(self):
		return {}
	def processActivitiesData(self, importer):
		damage, healing = self.damage.splitTypes(['healing', 'temphp'])
		healing = healing.parts[0] if len(healing.parts) else None

		return {
			"action_type": self.action_type,
			# "name": "",
			"activation": {
				"type": self.activation,
				"cost": 1 if self.activation else None
			},
			# "consumption": {},
			"description": { "value": self.description },
			"duration": {
				"value": self.duration_value,
				"units": self.duration_unit
			},
			# "effects": {},
			"range": {
				"value": self.range_short,
				"long": self.range_long or None,
				"units": self.range_unit or 'ft',
			},
			"target": {
				"value": self.target_value,
				"width": None,
				"units": self.target_unit,
				"type": self.target_type
			},
			# "uses": {},

			"attack": {
				"ability": "",
				"bonus": "",
				"critical": { "threshold": None },
				"flat": False,
				"type": {
					"value": 'melee',
					"classification": 'spell',
				},
			},
			"check": {
				"ability": "",
				"associated": [],
				"dc": {
					"calculation": "",
					"formula": "",
				}
			},
			"damage": damage,
			"effects": {},
			"enchant": {},
			"healing": healing,
			"save": {
				"ability": self.save,
				"dc": {
					"calculation": "" if self.save_dc else "spellcasting",
					"formula": self.save_dc or ""
				}
			},
			"roll": { "formula": self.formula },
			"properties": self.p_properties,
		}

	# templates.ItemDescription
	# getDescription - NotImplemented

	# templates.Identifiable

	# template.ItemType
	def getCategory(self):
		return None
	def getSubcategory(self):
		return None
	def getBaseItemName(self):
		return re.sub(r'\'|\s+|\([^)]*\)', '', self.raw_name.lower());

	# template.PhysicalItem
	def getWeight(self):
		if type(self.raw_weight) == int: return self.raw_weight
		div = re.match(r'(\d+)/(\d+)', self.raw_weight)
		if div: return int(div.group(1)) / int(div.group(2))
	def getPrice(self):
		return self.raw_cost

	# templates.EquippableItem
