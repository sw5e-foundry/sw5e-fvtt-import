import sw5e.Entity, utils.text, utils.config, utils.object
import re, json, copy

class EnhancedItem(sw5e.Entity.Item):
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

		self.raw_subtypeType = \
			utils.text.clean(raw_item, utils.text.lowerCase(self.raw_type)+'Type') or \
			utils.text.clean(raw_item, f'enhanced{self.raw_type}Type') or \
			utils.text.clean(raw_item, f'itemModificationType') or 'None'
		self.raw_subtypeTypeEnum = \
			utils.text.raw(raw_item, f'{utils.text.lowerCase(self.raw_type)}TypeEnum') or \
			utils.text.raw(raw_item, f'enhanced{self.raw_type}TypeEnum') or \
			utils.text.raw(raw_item, f'itemModificationTypeEnum') or 0


	def process(self, importer):
		super().process(importer)

		self.is_modification = self.raw_type.endswith('Modification') or self.raw_type in ('CyberneticAugmentation', 'DroidCustomization')
		self.base_name = self.getBaseName()
		self.base_item = self.getBaseItem(importer)

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_unit, self.target_type = self.getTarget()
		self.range_value, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction()
		self.attack_bonus, self.damage_bonus = self.getAttackBonus()
		self.activation = self.getActivation()
		self.rarity = self.getRarity()
		self.modificationItemType = self.getModificationItemType()
		self.properties = self.getProperties()

	def getActivation(self):
		return utils.text.getActivation(self.raw_text, self.uses, self.recharge)

	def getDuration(self):
		return utils.text.getDuration(self.raw_text, self.raw_name)

	def getTarget(self):
		return utils.text.getTarget(self.raw_text, self.raw_name)

	def getRange(self):
		return utils.text.getRange(self.raw_text, self.raw_name)

	def getUses(self):
		return utils.text.getUses(self.raw_text, self.raw_name)

	def getAction(self):
		return utils.text.getAction(self.raw_text, self.raw_name)

	def getAttackBonus(self):
		if match := re.search(r'you (?:have|gain) a \+(?P<atk>\d+) (?:bonus )?to attack rolls and deal an additional (?P<dmg>\d*d\d+) damage (?:with (?:this|your unarmed strikes))?', self.raw_text.lower()):
			return (match["atk"], match["dmg"])
		if match := re.search(r'you (?:have|gain) a \+(?P<bonus>\d+) (?:bonus )?to (?P<atk>attack)?(?: and )?(?P<dmg>damage)? rolls (?:(?:made )?with (?:this|your unarmed strikes))?', self.raw_text.lower()):
			return (match["bonus"] if match[opt] else 0 for opt in ('atk', 'dmg'))
		if match := re.search(r'you (?:have|gain) a \+(?P<bonus>\d+) (?:bonus )?to (?P<up>attack|damage) rolls and a -(?P<penalty>\d+) penalty to (?:attack|damage) rolls (?:(?:made )?with (?:this|your unarmed strikes))?', self.raw_text.lower()):
			return (match["bonus"] if match["up"] == opt else "-"+match["penalty"] for opt in ('attack', 'damage'))
		return 0, 0

	def getRarity(self):
		return self.raw_rarityText

	def getModificationItemType(self):
		if self.raw_subtype in ('armor', 'clothing', 'focusgenerator', 'wristpad'): return 'equipment'
		elif self.raw_subtype in ('blaster', 'vibroweapon', 'lightweapon'): return 'weapon'

	def getProperties(self):
		target_type = self.modificationItemType or (self.base_item and self.base_item.getType())

		if target_type == 'equipment':
			if self.raw_type == 'Focus': properties_list = utils.config.casting_properties
			else: properties_list = utils.config.armor_properties
		elif target_type == 'weapon':
			properties_list = utils.config.weapon_properties
		else:
			return {}

		return utils.text.getProperties(self.raw_text, properties_list, needs_end=True)

	def getBaseName(self):
		# Remove any modifiers to it's name
		name = re.sub(r'\s*\([^()]*\)$', '', self.raw_name)
		name = re.sub(r'\s*Mk \w+$', '', name)
		name = re.sub(r' Chassis$', '', name)
		return name

	def getBaseItem(self, importer):
		if not importer: return None
		if self.is_modification: return None
		if self.raw_subtypeType.startswith('Any'): return None

		get_data = {}
		if self.raw_subtypeType == 'Specific':
			get_data = {
				'name': self.raw_subtype.title(),
				'equipmentCategory': self.raw_type.title(),
			}
		elif self.raw_name != self.base_name:
			get_data = {
				'name': self.base_name,
				'equipmentCategory': utils.config.enhanced_equipment_mappings[f'{self.raw_type}-{self.raw_subtype}'],
			}
		else:
			return None

		if get_data["equipmentCategory"] == None:
			return None
		elif type(get_data["equipmentCategory"]) is tuple:
			for category in get_data["equipmentCategory"]:
				data = { k:v for k,v in get_data.items() }
				data["equipmentCategory"] = category
				if base_item := importer.get('equipment', data=data):
					return base_item
		elif base_item := importer.get('equipment', data=get_data):
			return base_item
		elif not self.base_name in (utils.config.enhanced_item_icons + utils.config.enhanced_item_no_icons):
			print(f"		Failed to find base item for '{self.raw_name}', {self.base_name=}")

	def getDescription(self, base_text = None):
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
		if base_text:
			base_text = utils.text.markdownToHtml(f'### {self.base_item.name}') + '\n' + base_text
			text = text + '\n<p>&nbsp;</p>\n' + base_text
		header = re.sub(r'([a-z])([A-Z])', r'\1 \2', self.raw_type)
		header = f'##### {header}'
		if self.raw_subtype:
			header += f' ({self.raw_subtype.title()})'
		text = f'{utils.text.markdownToHtml(header)}\n {text}'
		return text

	def getImg(self, importer=None):
		name = self.base_name

		# First check if it's an item with a specific icon for it's enhanced version
		if name in utils.config.enhanced_item_icons:
			name = utils.text.slugify(name)
			return f'systems/sw5e/packs/Icons/Enhanced%20Items/{name}.webp'

		# Use the base item's icon
		if self.base_item:
			return self.base_item.getImg(importer=importer)

		# Use the modification subtype icons
		if self.is_modification:
			subtype = self.raw_subtype
			if self.raw_type == 'CyberneticAugmentation': subtype = f'CyberneticMod'
			elif self.raw_type == 'DroidCustomization': subtype = f'DroidMod'
			return f'systems/sw5e/packs/Icons/Modifications/{subtype.replace(" ", "").capitalize()}Mod.svg'

		# Otherwise use the default item bag icon
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
		item_type = mapping[self.raw_typeEnum]

		return item_type or 'loot'

	def getDataSpecific(self, importer):
		def choose(base, enhanced, field, default):
			if field in base and base[field] != default: return base[field]
			if enhanced != default: return enhanced
			return default

		superdata = super().getData(importer)[0]
		data = self.base_item.getData(importer)

		for item in data:
			mode = (re.search(r'\.mode-(.*)', item["flags"]["sw5e-importer"]["uid"]) or [None,None])[1]

			for key in superdata:
				if key in ("system", "img"): continue
				item[key] = copy.deepcopy(superdata[key])

			if self.getImg(importer=importer) != 'icons/svg/item-bag.svg':
				item["img"] = self.getImg(importer=importer)

			if mode:
				item["name"] += f' ({mode.title()})'
				item["flags"]["sw5e-importer"]["uid"] += f'.mode-{mode}'

			item["system"]["description"] = {
				"value": self.getDescription(base_text = item["system"]["description"]["value"])
			}
			item["system"]["source"] = self.raw_contentSource
			item["system"]["attunement"] = 1 if self.raw_requiresAttunement else 0
			item["system"]["rarity"] = self.rarity

			activation = choose(item["system"]["activation"], self.activation, "type", 'none')
			item["system"]["activation"] = {
				"type": activation,
				"cost": 1 if activation != 'none' else None
			}
			item["system"]["duration"] = {
				"value": choose(item["system"]["duration"], self.duration_value, "value", None),
				"units": choose(item["system"]["duration"], self.duration_unit, "units", 'inst'),
			}
			item["system"]["target"] = {
				"value": choose(item["system"]["target"], self.target_value, "value", None),
				"width": None,
				"units": choose(item["system"]["target"], self.target_unit, "units", ''),
				"type": choose(item["system"]["target"], self.target_type, "type", ''),
			}
			item["system"]["range"] = {
				"value": choose(item["system"]["range"], self.range_value, "value", None),
				"long": choose(item["system"]["range"], None, "long", None),
				"units": choose(item["system"]["range"], self.range_unit, "units", ''),
			}
			if "per" not in item["system"]["uses"] or item["system"]["uses"]["per"] == None:
				item["system"]["uses"] = {
					"value": None,
					"max": self.uses,
					"per": self.recharge
				}
			#	item["system"]["consume"] = {}
			#	item["system"]["ability"] = ''

			item["system"]["properties"] = {**item["system"]["properties"], **self.properties}

			item["system"]["actionType"] = choose(item["system"], self.action_type, "actionType", 'other')
			if self.attack_bonus:
				if item["system"]["attackBonus"]: item["system"]["attackBonus"] += f' + {self.attack_bonus}'
				else: item["system"]["attackBonus"] = self.attack_bonus
			#	item["system"]["chatFlavor"] = ''
			#	item["system"]["critical"] = None
			item["system"]["damage"] = {
				"parts": (item["system"]["damage"]["parts"] if "parts" in item["system"]["damage"] else []) + self.damage["parts"],
				"versatile": choose(item["system"]["damage"], self.damage["versatile"], "versatile", '')
			}

			if self.damage_bonus and item["system"]["damage"]["parts"]:
				item["system"]["damage"]["parts"][0][0] += f' + {self.damage_bonus}'
				if item["system"]["damage"]["versatile"]: item["system"]["damage"]["versatile"] += f' + {self.damage_bonus}'

			item["system"]["formula"] = choose(item["system"], self.formula, "formula", '')
			item["system"]["save"] = {
				"ability": choose(item["system"]["save"], self.save, "ability", ''),
				"dc": None,
				"scaling": "none"
			}

			item = self.applyDataAutoTarget(item)
			item = self.applyDataSubtype(item)

			#	item["system"]["recharge"] = ''

		return data

	def getData(self, importer):
		if self.base_item: return self.getDataSpecific(importer)

		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription() }
		data["system"]["source"] = self.raw_contentSource
		data["system"]["attunement"] = 1 if self.raw_requiresAttunement else 0
		data["system"]["rarity"] = self.rarity

		if self.activation: data["system"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation != 'none' else None
		}
		if self.duration_value or self.duration_unit: data["system"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		if self.target_value or self.target_unit or self.target_type: data["system"]["target"] = {
			"value": self.target_value,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		if self.range_value or self.range_unit: data["system"]["range"] = {
			"value": self.range_value,
			"long": None,
			"units": self.range_unit
		}
		if self.uses or self.recharge: data["system"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}
		#	item["system"]["consume"] = {}
		#	item["system"]["ability"] = ''

		if self.action_type: data["system"]["actionType"] = self.action_type
		if self.attack_bonus: data["system"]["attackBonus"] = self.attack_bonus
		if self.damage_bonus: data["system"]["damageBonus"] = self.damage_bonus
		#	item["system"]["chatFlavor"] = ''
		data["system"]["critical"] = {
			"threshold": None,
			"damage": ""
		}
		if self.damage: data["system"]["damage"] = {
			"parts": self.damage["parts"],
			"versatile": self.damage["versatile"]
		}
		if self.formula: data["system"]["formula"] = self.formula
		if self.save: data["system"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": "flat" if self.save_dc else "power"
		}

		data["system"]["properties"] = self.properties

		self.applyDataAutoTarget(data)
		self.applyDataSubtype(data)

		#	data["system"]["recharge"] = ''

		return [data]

	def applyDataAutoTarget(self, data):
		if self.getType() == 'Weapon':
			if 'smr' in self.properties and type(auto := self.properties["smr"].split(', ')) == list:
				mod = (int(auto[0]) - 10) // 2
				prof = int(auto[1])
				data["system"]["ability"] = 'str'
				data["system"]["attackBonus"] = f'{mod} - @abilities.str.mod + {prof} - @attributes.prof'
				data["system"]["damage"]["parts"][0][0] = f'{self.base_item.raw_damageNumberOfDice}d{self.base_item.raw_damageDieType} + {mod}'
				data["system"]["proficient"] = True
		return data

	def applyDataSubtype(self, data):
		if self.base_item:
			return data
		elif self.raw_type == 'AdventuringGear':
			data["system"]["armor"] = {
				"value": None,
				"dex": None,
			}
			if self.raw_subtype in ('body', 'feet', 'hands', 'head', 'shoulders', 'waist', 'wrists', 'forearms', 'forearm', 'legs'):
				data["system"]["armor"]["type"] = 'clothing'
			elif self.raw_subtype in (None, '', 'finger', 'other', 'neck', 'back', 'wrist'):
				data["system"]["armor"]["type"] = 'trinket'
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Armor':
			if self.raw_subtypeType in ('AnyHeavy', 'Any'):
				data["system"]["armor"] = {
					"value": 16,
					"type": 'heavy',
					"dex": 0,
				}
			elif self.raw_subtypeType == 'AnyMedium':
				data["system"]["armor"] = {
					"value": 14,
					"type": 'medium',
					"dex": 2,
				}
			elif self.raw_subtypeType == 'AnyLight':
				data["system"]["armor"] = {
					"value": 11,
					"type": 'light',
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
			data["system"]["armor"] = {
				"value": 2,
				"type": 'shield',
				"dex": None,
			}
			if self.raw_subtypeType == 'Light':
				data["system"]["armor"]["value"] = 1
			elif self.raw_subtypeType in ('Medium', 'Any'):
				data["system"]["armor"]["value"] = 2
			elif self.raw_subtypeType == 'Heavy':
				data["system"]["armor"]["value"] = 3
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Weapon':
			if not utils.object.getProperty(data, 'system.activation.type'):
				utils.object.setProperty(data, 'system.activation', { "type": 'action', "cost": 1 }, force=True)
			if not utils.object.getProperty(data, 'system.target.type'):
				utils.object.setProperty(data, 'system.target', { "value": 1 , "type": 'enemy' }, force=True)

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
				if ("weaponType" not in data["system"]) or (not data["system"]["weaponType"]):
					data["system"]["weaponType"] = 'improv'
			elif self.raw_subtypeType in ('AnyBlaster', 'AnyBlasterWithProperty'):
				data["system"]["actionType"] = 'rwak'
				data["system"]["weaponType"] = 'simpleB'
			elif self.raw_subtypeType in ('AnyVibroweapon', 'AnyVibroweaponWithProperty'):
				data["system"]["actionType"] = 'mwak'
				data["system"]["weaponType"] = 'simpleVW'
			elif self.raw_subtypeType in ('AnyLightweapon', 'AnyLightweaponWithProperty'):
				data["system"]["actionType"] = 'mwak'
				data["system"]["weaponType"] = 'simpleLW'
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
			data["system"]["modificationItemType"] = self.modificationItemType

			data["system"]["modificationType"] = 'focusgenerator' if self.raw_subtype == 'focus generator' else self.raw_subtype
			data["system"]["-=modificationSlot"] = None

			data["system"]["properties"]["indeterminate"] = { key: False for key in self.properties.keys() }
		else:
			raise ValueError(self.raw_name, self.raw_type)

		return data

	def getFile(self, importer):
		return f'Enhanced{self.raw_type}'
