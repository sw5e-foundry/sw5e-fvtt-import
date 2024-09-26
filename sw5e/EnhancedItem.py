import sw5e.Entity, sw5e.Equipment, utils.text, utils.config, utils.object
import re, json, copy

class EnhancedItem(
	sw5e.Entity.Item,
	sw5e.templates.Activities,
	sw5e.templates.ItemDescription,
	sw5e.templates.ItemType,
	sw5e.templates.Identifiable,
	sw5e.templates.PhysicalItem,
	sw5e.templates.EquippableItem,
):
	def getAttrs(self):
		return super().getAttrs() + [
			"name",
			"typeEnum",
			"type",
			"rarityOptionsEnum",
			"rarityOptions",
			"rarityText",
			"searchableRarity",
			"requiresAttunement",
			"valueText",
			"text",
			"hasPrerequisite",
			"prerequisite",
			"subtype",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
		]

	def load(self, raw_item):
		super().load(raw_item)

		self.raw_subtypeTypeEnum = 0
		self.raw_subtypeType = 'None'
		for key in [utils.text.lowerCase(self.raw_type)+'Type', f'enhanced{self.raw_type}Type', f'itemModificationType']:
			if enum := utils.text.raw(raw_item, f'{key}Enum'):
				self.raw_subtypeTypeEnum = enum
				self.raw_subtypeType = utils.text.clean(raw_item, key)
				break

		self.is_modification = self.raw_type.endswith('Modification') or self.raw_type in ('CyberneticAugmentation', 'DroidCustomization')
		self.modification_item_type = self.getModificationItemType()
		self.modifiable_item = self.getModifiableItem() or False

	def getModificationItemType(self):
		if self.raw_subtype in ('armor', 'clothing', 'focusgenerator', 'wristpad'): return 'equipment'
		elif self.raw_subtype in ('blaster', 'vibroweapon', 'lightweapon'): return 'weapon'

	def getModifiableItem(self):
		if self.is_modification: return
		if self.raw_name.find("Chassis") != -1:
			return {
				'chassis': 'chassis',
				'augmentSlots': utils.config.chassis_slots.get(self.getRarity(), 4) - 4
			}



	def process(self, importer):
		super().process(importer)

		self.base_name = self.getBaseName()
		self.base_item = self.getBaseItem(importer)

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_unit, self.target_type = self.getTarget()
		self.range_short, self.range_long, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.attack_bonus, self.damage_bonus, text = self.getAttackBonus()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction(text)
		self.activation = self.getActivation()
		self.properties = self.getProperties()

	def getActivation(self):
		default = self.base_item.activation if self.base_item else None
		return utils.text.getActivation(self.raw_text, self.uses, self.recharge, default=default)

	def getDuration(self):
		default=(self.base_item.duration_unit, self.base_item.duration_value) if self.base_item else (None, 'inst')
		return utils.text.getDuration(self.raw_text, self.raw_name, default=default)

	def getTarget(self):
		default=(self.base_item.target_value, self.base_item.target_unit, self.base_item.target_type) if self.base_item else (None, '', '')
		return utils.text.getTarget(self.raw_text, self.raw_name, default=default)

	def getRange(self):
		default=(self.base_item.range_short, self.base_item.range_unit) if self.base_item else (None, '')
		short, unit = utils.text.getRange(self.raw_text, self.raw_name, default=default)
		return short, self.base_item.range_long if self.base_item else None, unit

	def getUses(self):
		default=(self.base_item.uses, self.base_item.recharge) if self.base_item else (None, None)
		return utils.text.getUses(self.raw_text, self.raw_name, default=default)

	def getAction(self, text):
		default=(
			self.base_item.action_type,
			self.base_item.damage,
			self.base_item.formula,
			self.base_item.save,
			self.base_item.save_dc,
			{}
		) if self.base_item else (
			'',
			{ "base": { "parts": [] }, "versatile": { "parts": [] } },
			'',
			'',
			None,
			{ "mode": 'none'}
		)
		action_type, damage, other_formula, save, save_dc, scaling = utils.text.getAction(text, self.raw_name, default=default)
		return action_type, damage, other_formula, save, save_dc, scaling


	def getAttackBonus(self):
		text = self.raw_text.lower()
		def replaceText(_text, _match):
			return _text[:_match.start()] + 'FORMULA' + _text[_match.end():]
		if match := re.search(r'you (?:have|gain) a \+(?P<atk>\d+) (?:bonus )?to attack rolls and deal an additional (?P<dmg>\d*d\d+) damage (?:with (?:this|your unarmed strikes))?', text):
			return (match["atk"], match["dmg"], replaceText(text, match))
		if match := re.search(r'you (?:have|gain) a \+(?P<bonus>\d+) (?:bonus )?to (?P<atk>attack)?(?: and )?(?P<dmg>damage)? rolls (?:(?:made )?with (?:this|your unarmed strikes))?', text):
			return tuple(match["bonus"] if match[opt] else 0 for opt in ('atk', 'dmg')) + (replaceText(text, match),)
		if match := re.search(r'you (?:have|gain) a \+(?P<bonus>\d+) (?:bonus )?to (?P<up>attack|damage) rolls and a -(?P<penalty>\d+) penalty to (?:attack|damage) rolls (?:(?:made )?with (?:this|your unarmed strikes))?', text):
			return tuple(match["bonus"] if match["up"] == opt else "-"+match["penalty"] for opt in ('attack', 'damage')) + (replaceText(text, match),)
		return 0, 0, text

	def getPropertiesList(self):
		target_type = self.modification_item_type or (self.base_item and self.base_item.getType())

		if target_type == 'equipment':
			if self.raw_type == 'Focus': properties_list = utils.config.casting_properties
			else: properties_list = utils.config.armor_properties
		elif target_type == 'weapon':
			properties_list = utils.config.weapon_properties
		else:
			return {}

	def getProperties(self):
		properties_list = self.getPropertiesList()

		properties = utils.text.getProperties(self.raw_text, properties_list, needs_end=True) if properties_list else {}

		if self.base_item and self.base_item.p_properties: return { **self.base_item.p_properties, **properties }
		return properties

	def getBaseName(self):
		# Remove any modifiers to it's name
		name = re.sub(r'\s*\([^()]*\)$', '', self.raw_name)
		name = re.sub(r'\s*Mk \w+$', '', name)
		name = re.sub(r' Chassis$', '', name)
		name = re.sub(r'(Adept|Ancient|Apprentice|Journeyman|Master|Novice) ', '', name)
		name = re.sub(r'(Knight\'s|Master\'s|Padawan\'s) ', '', name)
		name = re.sub(r'(Acolyte\'s|Lord\'s|Warrior\'s) ', '', name)
		return name

	def getBaseItem(self, importer):
		if not importer: return None
		if self.is_modification: return None

		get_data = {}
		if self.raw_subtypeType == 'Specific':
			get_data = {
				'name': self.raw_subtype.title(),
				'equipmentCategory': (self.raw_type.title(),),
			}
		elif self.raw_name != self.base_name:
			get_data = {
				'name': self.base_name.lower(),
				'equipmentCategory': utils.config.enhanced_equipment_mappings.get(f'{self.raw_type}-{self.raw_subtype}', 'NOPE'),
			}
		else:
			return None

		if get_data["equipmentCategory"] == 'NOPE':
			raise ValueError(self.raw_name, self.base_name, self.raw_type, self.raw_subtype)
		elif get_data["equipmentCategory"] == None:
			return None
		elif type(get_data["equipmentCategory"]) is tuple:
			for category in get_data["equipmentCategory"]:
				data = { k:v for k,v in get_data.items() }
				data["equipmentCategory"] = category
				equipment_type = sw5e.Equipment.Equipment.getEquipmentType(data)
				if base_item := importer.get(equipment_type, data=data):
					return base_item

		if self.raw_subtypeType.startswith('Any'): return None
		if self.base_name in (utils.config.enhanced_item_icons + utils.config.enhanced_item_no_icons): return None
		if self.modifiable_item: return None
		print(f"		Failed to find base item for '{self.raw_name}', {get_data=}")
		raise ValueError()

	def getEquipmentCategory(self):
		if self.base_item:
			return self.base_item.getCategory(), self.base_item.getSubcategory()

		if self.raw_type == 'AdventuringGear':
			if self.raw_subtype in ('body', 'feet', 'hands', 'head', 'shoulders', 'waist', 'wrists', 'forearms', 'forearm', 'legs'):
				return 'clothing', None
			elif self.raw_subtype in (None, '', 'finger', 'other', 'neck', 'back', 'wrist'):
				return 'trinket', None
		elif self.raw_type == 'Armor':
			if self.raw_subtypeType in ('AnyHeavy', 'Any'):
				return 'heavy', None
			elif self.raw_subtypeType == 'AnyMedium':
				return 'medium', None
			elif self.raw_subtypeType == 'AnyLight':
				return 'light', None
		elif self.raw_type == 'Consumable':
			if self.raw_subtype in ('poison',): return self.raw_subtype, None
			elif self.raw_subtype in ('adrenal', 'stimpac'): return 'substance', self.raw_subtype
			elif self.raw_subtype == 'substance':
				if re.search(r'spice', self.base_name.lower()) or re.search(r'spice', self.raw_text.lower()):
					return 'substance', 'spice'
				elif re.search(r'alcoholic beverage|liquor|grog|spirit', self.raw_text.lower()):
					return 'technology', 'beverage'
				return 'substance', None
			elif self.raw_subtype == 'technology':
				if re.search(r'spike', self.base_name.lower()):
					return 'technology', 'spike'
				elif re.search(r'teleporter', self.base_name.lower()):
					return 'technology', 'teleporter'
				elif re.search(r'repair kit', self.base_name.lower()):
					return 'medical', 'droid'
				elif re.search(r'this adrenal', self.raw_text.lower()):
					return 'substance', 'adrenal'
				return 'technology', None
			elif self.raw_subtype == 'barrier':
				if self.base_name.lower().startswith('physical'):
					return 'barrier', 'physical'
				if self.base_name.lower().startswith('environmental'):
					return 'barrier', 'environmental'
				return 'barrier', None
			elif self.raw_subtype == 'medpac':
				if re.search(r'vitapac', self.base_name.lower()):
					return 'medical', 'vitapac'
				return 'medical', 'medpac'
			raise ValueError(self.name, self.raw_subtype)
			return None, None
		elif self.raw_type == 'Shield':
			return 'shield', None
		elif self.raw_type == 'Weapon':
			if self.raw_subtypeType in ('AnyBlaster', 'AnyBlasterWithProperty'):
				return 'simpleB', None
			elif self.raw_subtypeType in ('AnyVibroweapon', 'AnyVibroweaponWithProperty'):
				return 'simpleVW', None
			elif self.raw_subtypeType in ('AnyLightweapon', 'AnyLightweaponWithProperty'):
				return 'simpleLW', None
			else:
				return 'improv', None
		elif self.is_modification:
			return False, False

		return None, None

	def getImg(self, importer=None):
		name = self.base_name

		# First check if it's an item with a specific icon for it's enhanced version
		if name in utils.config.enhanced_item_icons:
			name = utils.text.slugify(name)
			return f'modules/sw5e/icons/packs/Enhanced%20Items/{name}.webp'

		# Use the base item's icon
		if self.base_item:
			if name in utils.config.enhanced_item_no_icons:
				print('item in enhanced_item_no_icons but has base item:', self.name, self.base_name)
			return self.base_item.getImg(importer=importer)

		# Use the modification subtype icons
		if self.is_modification:
			subtype = self.raw_subtype.replace(" ", "").capitalize()
			if self.raw_type == 'CyberneticAugmentation': subtype = f'Cybernetic'
			elif self.raw_type == 'DroidCustomization': subtype = f'Droid'
			if subtype != 'Augment': subtype = f'{subtype}Mod'
			return f'modules/sw5e/icons/packs/Modifications/{subtype}.webp'

		# Otherwise use the default item bag icon
		if name in utils.config.enhanced_item_no_icons:
			return 'icons/svg/item-bag.svg'

		print(f'		Enhanced item with no icon, but not in the no icon list. {name=}')
		return 'icons/svg/item-bag.svg'

	def getType(self):
		mapping = [
			None, ## 0 = Unknown
			'equipment', ## 1 = AdventuringGear
			'equipment', ## 2 = Armor
			'consumable', ## 3 = Consumable
			'modification', ## 4 = CyberneticAugmentation
			'modification', ## 5 = DroidCustomization
			'equipment', ## 6 = Focus
			'modification', ## 7 = ItemModification
			'equipment', ## 8 = Shield
			'weapon', ## 9 = Weapon
			None, ## 10 = ?
			'loot', ## 11 = ShipArmor
			'loot', ## 12 = ShipShield
			'loot', ## 13 = ShipWeapon
			'modification', ## 14 = BlasterModification
			'modification', ## 15 = ClothingModification
			'modification', ## 16 = WristpadModification
			'modification', ## 17 = ArmorModification
			'modification', ## 18 = VibroweaponModification
			'modification', ## 19 = LightweaponModification
			'modification', ## 20 = FocusGeneratorModification
		]
		return mapping[self.raw_typeEnum] or 'loot'

	def getData(self, importer):
		data = super().getData(importer)[0]

		# templates.Activities
		# templates.ItemDescription
		# templates.Identifiable
		# templates.ItemType
		# templates.PhysicalItem
		# templates.EquippableItem
		## templates.Mountable -- NotImplemented

		if self.modifiable_item: data["system"]["modify"] = self.modifiable_item

		if self.properties:
			properties = { key: value for key, value in self.properties.items() if value }
			utils.object.setProperty(data, 'flags.sw5e.properties', properties, force=True)
			utils.object.setProperty(data, 'system.properties', list(properties.keys()), force=True)

		self.applyDataSubtype(data)

		return [data]

	def applyDataAutoTarget(self, data, burst_or_rapid=False):
		if self.getType() == 'Weapon':
			if 'smr' in self.properties and type(smr := self.properties["smr"].split(', ')) == list:
				mod = (int(smr[0]) - 10) // 2
				prof = int(smr[1])

				if burst_or_rapid:
					data["save"]["dc"]["calculation"] = ''
					data["save"]["dc"]["formula"] = 8 + mod + prof + self.attack_bonus
					data["save"]["ability"] = 'dex'
				else:
					data["attack"]["bonus"] = f'{mod} + {prof}'
					data["attack"]["flat"]: True

				data["damage"]["base"]["parts"][0][0] = f'{self.base_item.raw_damageNumberOfDice}d{self.base_item.raw_damageDieType} + {mod}'

		return data

	def applyDataSubtype(self, data):
		if self.base_item:
			item_type = self.base_item.getType()
			if item_type == 'container':
				# TODO: Read capacity from the item's description
				# utils.object.setProperty(data, 'system.capacity.type', 'weight')
				# utils.object.setProperty(data, 'system.capacity.value', 0)
				pass
			elif item_type == 'consumable':
				# TODO: Read these from description
				# utils.object.setProperty(data, 'system.damage.base', 1)
				# utils.object.setProperty(data, 'system.damage.replace', False)
				# utils.object.setProperty(data, 'system.magicalBonus', 0)
				# utils.object.setProperty(data, 'system.uses.autoDestroy', True)
				pass
			elif item_type == 'equipment':
				utils.object.setProperty(data, 'system.armor', self.base_item.armor)
				utils.object.setProperty(data, 'system.strength', self.base_item.raw_strengthRequirement)
			elif item_type == 'loot':
				pass
			elif item_type == 'tool':
				pass
			elif item_type == 'weapon':
				utils.object.setProperty(data, 'system.weaponClass', self.base_item.weapon_class, force=True)
				utils.object.setProperty(data, 'system.damage', self.base_item.damage, force=True)
				utils.object.setProperty(data, 'flags.sw5e.reload.types', self.base_item.ammo_types, force=True)


		if self.base_item:
			pass
		elif self.raw_type == 'AdventuringGear':
			pass
		elif self.raw_type == 'Armor':
			if self.raw_subtypeType in ('AnyHeavy', 'Any'):
				data["system"]["armor"] = {
					"value": 16,
					"dex": 0,
				}
			elif self.raw_subtypeType == 'AnyMedium':
				data["system"]["armor"] = {
					"value": 14,
					"dex": 2,
				}
			elif self.raw_subtypeType == 'AnyLight':
				data["system"]["armor"] = {
					"value": 11,
					"dex": None,
				}
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Consumable':
			pass
		elif self.raw_type == 'CyberneticAugmentation':
			data["system"]["modificationType"] = 'cybernetic'
		elif self.raw_type == 'DroidCustomization':
			data["system"]["modificationType"] = 'droidcustomization'
		elif self.raw_type == 'Shield':
			utils.object.setPropertyWeak(data, 'system.armor.dex', None)
			if self.raw_subtypeType == 'Light':
				utils.object.setPropertyWeak(data, 'system.armor.value', 1)
			elif self.raw_subtypeType in ('Medium', 'Any'):
				utils.object.setPropertyWeak(data, 'system.armor.value', 2)
			elif self.raw_subtypeType == 'Heavy':
				utils.object.setPropertyWeak(data, 'system.armor.value', 3)
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Weapon':
			utils.object.setPropertyWeak(data, 'system.activation', { "type": 'action', "cost": 1 })
			utils.object.setPropertyWeak(data, 'system.target', { "value": 1 , "type": 'enemy' })

			if self.raw_subtypeType in ('AnyWithProperty', 'AnyBlasterWithProperty', 'AnyVibroweaponWithProperty', 'AnyLightweaponWithProperty'):
				print(f"	'{self.raw_subtypeType}' enhanced weapon detected. This kind of item is not supported since there currently no examples to know what they should look like.")
				print(f'{self.raw_name=}')
				print(f'{self.raw_type=}')
				print(f'{self.raw_subtype=}')
				print(f'{self.raw_subtypeType=}')
				print(f'{self.raw_text=}')

			if self.raw_subtypeType in ('Any', 'AnyWithProperty'):
				if data["system"]["actionType"] == 'other':
					data["system"]["actionType"] = 'mwak'
			elif self.raw_subtypeType in ('AnyBlaster', 'AnyBlasterWithProperty'):
				data["system"]["actionType"] = 'rwak'
			elif self.raw_subtypeType in ('AnyVibroweapon', 'AnyVibroweaponWithProperty'):
				data["system"]["actionType"] = 'mwak'
			elif self.raw_subtypeType in ('AnyLightweapon', 'AnyLightweaponWithProperty'):
				data["system"]["actionType"] = 'mwak'
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Valuable':
			print("	'Valuable' enhanced item detected. This kind of item is not supported since there currently no examples to know what they should look like.")
			print(f'{self.raw_name=}')
			print(f'{self.raw_type=}')
			print(f'{self.raw_subtype=}')
			print(f'{self.raw_subtypeType=}')
			print(f'{self.raw_text=}')
		elif self.raw_type == 'ShipArmor':
			## TODO: change this one ships are supported
			pass
		elif self.raw_type == 'ShipShield':
			## TODO: change this one ships are supported
			pass
		elif self.raw_type == 'ShipWeapon':
			## TODO: change this one ships are supported
			pass
		elif self.is_modification:
			data["system"]["modificationItemType"] = self.modification_item_type

			# data["system"]["properties"]["indeterminate"] = { key: False for key in self.properties.keys() }
		else:
			raise ValueError(self.raw_name, self.raw_type)

		return data

	def getFile(self, importer):
		return f'Enhanced{self.raw_type}'


	# templates.Activities
	def getActivitiesData(self):
		return {}
	def processActivitiesData(self, importer):
		data = {
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
			"range": self.range_short,
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
				"classification": "spell",
				"flat": False,
				"type": "melee",
			},
			"check": {
				"ability": "",
				"associated": [],
				"dc": {
					"calculation": "",
					"formula": "",
				}
			},
			"damage": {
				"critical": { "allow": True },
				"parts": [dmg for dmg in self.damage["base"]["parts"] if dmg[1] not in ('healing', 'temphp')] if self.damage else [],
			},
			"versatile": self.damage["versatile"] if self.damage else {},
			"effects": {},
			"enchant": {},
			"healing": [heal for heal in self.damage["base"]["parts"] if heal[1] in ('healing', 'temphp')] if self.damage else [],
			"save": {
				"ability": self.save,
				"dc": {
					"calculation": "" if self.save_dc else "spell",
					"formula": self.save_dc or ""
				}
			},
			"roll": self.formula,
			"properties": self.properties,
		}
		self.applyDataAutoTarget(data)
		return data

	# templates.ItemDescription
	def getDescription(self):
		text = self.raw_text

		header = ''
		if self.raw_requiresAttunement:
			if text.startswith('_**Requires attunement'):
				match = re.search('\n', text)
				header, text = text[:match.end()], text[match.end():]
			else:
				header += f'_**Requires attunement**_\r\n'

		if self.raw_prerequisite:
			header += f'_Prerequisite: {self.raw_prerequisite}_\r\n'

		if header: header += '<hr/>\n'

		text = header + text

		text = utils.text.markdownToHtml(text)
		header = re.sub(r'([a-z])([A-Z])', r'\1 \2', self.raw_type)
		header = f'##### {header}'
		if self.raw_subtype:
			header += f' ({self.raw_subtype.title()})'
		text = f'{utils.text.markdownToHtml(header)}\n {text}'
		return text
	def processDescription(self, importer):
		if self.base_item and (base_text := self.base_item.description):
			base_text = utils.text.markdownToHtml(f'### {self.base_item.name}') + '\n' + base_text
			self.description = self.description + '\n<p>&nbsp;</p>\n' + base_text

	# templates.Identifiable

	# template.ItemType
	def getCategory(self):
		return None
	def getSubcategory(self):
		return None
	def getBaseItemName(self):
		return None
	def processCategory(self, importer):
		self.category, self.subcategory = self.getEquipmentCategory()
	def processBaseItemName(self, importer):
		self.baseItemName = self.base_item.name if self.base_item else None

	# template.PhysicalItem
	def getWeight(self):
		return None
	def getPrice(self):
		return None
	def getRarity(self):
		return utils.config.rarities[self.raw_rarityText.lower()]
	def processPrice(self, importer):
		if self.base_item: self.price = self.base_item.price

	# templates.EquippableItem
	def getAttunement(self):
		return 'required' if self.raw_requiresAttunement else ''
