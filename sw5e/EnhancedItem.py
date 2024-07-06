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

		self.raw_subtypeTypeEnum = 0
		self.raw_subtypeType = 'None'
		for key in [utils.text.lowerCase(self.raw_type)+'Type', f'enhanced{self.raw_type}Type', f'itemModificationType']:
			if enum := utils.text.raw(raw_item, f'{key}Enum'):
				self.raw_subtypeTypeEnum = enum
				self.raw_subtypeType = utils.text.clean(raw_item, key)
				break

		self.is_modification = self.raw_type.endswith('Modification') or self.raw_type in ('CyberneticAugmentation', 'DroidCustomization')
		self.rarity = self.getRarity()
		self.modification_item_type = self.getModificationItemType()
		self.modifiable_item = self.getModifiableItem() or False


	def process(self, importer):
		super().process(importer)

		self.base_name = self.getBaseName()
		self.base_item = self.getBaseItem(importer)
		self.category, self.subcategory = self.getEquipmentCategory()

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_unit, self.target_type = self.getTarget()
		self.range_value, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.attack_bonus, self.damage_bonus, text = self.getAttackBonus()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction(text)
		self.activation = self.getActivation()
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

	def getAction(self, text):
		return utils.text.getAction(text, self.raw_name)

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

	def getRarity(self):
		return self.raw_rarityText

	def getModificationItemType(self):
		if self.raw_subtype in ('armor', 'clothing', 'focusgenerator', 'wristpad'): return 'equipment'
		elif self.raw_subtype in ('blaster', 'vibroweapon', 'lightweapon'): return 'weapon'

	def getModifiableItem(self):
		if self.is_modification: return
		if self.raw_name.find("Chassis") != -1:
			return {
				'chassis': 'chassis',
				'augmentSlots': utils.config.chassis_slots.get(self.rarity, 4) - 4
			}

	def getProperties(self):
		target_type = self.modification_item_type or (self.base_item and self.base_item.getType())

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
				'equipmentCategory': self.raw_type.title(),
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
				if base_item := importer.get('equipment', data=data):
					return base_item
		elif base_item := importer.get('equipment', data=get_data):
			return base_item

		if self.raw_subtypeType.startswith('Any'): return None
		if self.base_name in (utils.config.enhanced_item_icons + utils.config.enhanced_item_no_icons): return None
		if self.modifiable_item: return None
		print(f"		Failed to find base item for '{self.raw_name}', {get_data=}")

	def getEquipmentCategory(self):
		if self.base_item:
			return self.base_item.category, self.base_item.subcategory

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
				if self.base_name.lower().startswith('enviromental'):
					return 'barrier', 'enviromental'
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
			if name in utils.config.enhanced_item_no_icons:
				print('item in enhanced_item_no_icons but has base item:', self.name, self.base_name)
			return self.base_item.getImg(importer=importer)

		# Use the modification subtype icons
		if self.is_modification:
			subtype = self.raw_subtype.replace(" ", "").capitalize()
			if self.raw_type == 'CyberneticAugmentation': subtype = f'Cybernetic'
			elif self.raw_type == 'DroidCustomization': subtype = f'Droid'
			if subtype != 'Augment': subtype = f'{subtype}Mod'
			return f'systems/sw5e/packs/Icons/Modifications/{subtype}.webp'

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

	def getDataSpecific(self, importer):
		def choose(base, enhanced, field, default):
			if enhanced != default: return enhanced
			if field in base: return base[field]
			return default

		superdata = super().getData(importer)[0]
		data = copy.deepcopy(self.base_item.getData(importer))

		for item in data:
			mode = (re.search(r'\.mode-(.*)', item["flags"]["sw5e-importer"]["uid"]) or [None,None])[1]

			for key in superdata:
				if key in ("system", "img"): continue
				item[key] = copy.deepcopy(superdata[key])

			if (img := self.getImg(importer=importer)) != 'icons/svg/item-bag.svg':
				item["img"] = img

			if mode:
				item["name"] += f' ({mode.title()})'
				item["flags"]["sw5e-importer"]["uid"] += f'.mode-{mode}'

			item["system"]["description"] = {
				"value": self.getDescription(base_text = item["system"]["description"]["value"])
			}
			item["system"]["source"] = { "custom": self.raw_contentSource }
			item["system"]["attunement"] = 'required' if self.raw_requiresAttunement else ''
			item["system"]["rarity"] = self.rarity

			if "activation" not in item["system"]: item["system"]["activation"] = {}
			activation = choose(item["system"]["activation"], self.activation, "type", None)
			item["system"]["activation"] = {
				"type": activation,
				"cost": 1 if activation != 'none' else None
			}
			if self.duration_value or (self.duration_unit != 'inst'):
				if "duration" not in item["system"]: item["system"]["duration"] = {}
				item["system"]["duration"] = {
					"value": choose(item["system"]["duration"], self.duration_value, "value", None),
					"units": choose(item["system"]["duration"], self.duration_unit, "units", 'inst'),
				}
			if self.target_value or self.target_unit or self.target_type:
				if "target" not in item["system"]: item["system"]["target"] = {}
				item["system"]["target"] = {
					"value": choose(item["system"]["target"], self.target_value, "value", None),
					"width": None,
					"units": choose(item["system"]["target"], self.target_unit, "units", ''),
					"type": choose(item["system"]["target"], self.target_type, "type", ''),
				}
			if self.range_value or self.range_unit:
				if "range" not in item["system"]: item["system"]["range"] = {}
				item["system"]["range"] = {
					"value": choose(item["system"]["range"], self.range_value, "value", None),
					"long": choose(item["system"]["range"], None, "long", None),
					"units": choose(item["system"]["range"], self.range_unit, "units", ''),
				}

			if self.uses or self.recharge:
				if "uses" not in item["system"]: item["system"]["uses"] = {}
				if "per" not in item["system"]["uses"]: item["system"]["uses"]["per"] = None
				if item["system"]["uses"]["per"] == None:
					item["system"]["uses"] = {
						"value": None,
						"max": self.uses,
						"per": self.recharge
					}

			if self.properties:
				if "propertyValues" not in item["system"]: item["system"]["propertyValues"] = {}
				item["system"]["propertyValues"] = {**item["system"]["propertyValues"], **{key: value for key,value in self.properties.items() if value}}
				item["system"]["properties"] = list(item["system"]["propertyValues"].keys())

			if self.action_type:
				item["system"]["actionType"] = choose(item["system"], self.action_type, "actionType", 'other')

			if self.attack_bonus:
				if "attack" not in item["system"]: item["system"]["attack"] = { "bonus": '' }
				if item["system"]["attack"]["bonus"]: item["system"]["attack"]["bonus"] += f' + {self.attack_bonus}'
				else: item["system"]["attack"]["bonus"] = self.attack_bonus

			if (self.damage and (self.damage["parts"] or self.damage["versatile"])) or self.damage_bonus:
				if "damage" not in item["system"]: item["system"]["damage"] = {}
				if "parts" not in item["system"]["damage"]: item["system"]["damage"]["parts"] = []
				if "versatile" not in item["system"]["damage"]: item["system"]["damage"]["versatile"] = ''
				item["system"]["damage"] = {
					"parts": item["system"]["damage"]["parts"] + self.damage["parts"],
					"versatile": choose(item["system"]["damage"], self.damage["versatile"], "versatile", '')
				}

			if self.damage_bonus:
				if len(item["system"]["damage"]["parts"]): item["system"]["damage"]["parts"][0][0] += f' + {self.damage_bonus}'
				else: item["system"]["damage"]["parts"].append([f'{self.damage_bonus}', ''])
				if item["system"]["damage"]["versatile"]: item["system"]["damage"]["versatile"] += f' + {self.damage_bonus}'

			if self.formula:
				item["system"]["formula"] = choose(item["system"], self.formula, 'formula', '')

			if self.save or self.save_dc:
				if "save" not in item["system"]: item["system"]["save"] = {}
				item["system"]["save"] = {
					"ability": choose(item["system"]["save"], self.save, 'ability', ''),
					"dc": choose(item["system"]["save"], self.save_dc, 'dc', None),
					"scaling": choose(item["system"]["save"], 'flat' if self.save_dc else 'none', 'scaling', 'none')
				}

			item = self.applyDataAutoTarget(item, burst_or_rapid=mode in ('burst', 'rapid'))
			item = self.applyDataSubtype(item)

			#	item["system"]["recharge"] = ''

		return data

	def getData(self, importer):
		if self.base_item: return self.getDataSpecific(importer)

		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription() }
		data["system"]["source"] = { "custom": self.raw_contentSource }
		data["system"]["attunement"] = 'required' if self.raw_requiresAttunement else ''
		data["system"]["rarity"] = self.rarity

		if self.activation: data["system"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation != 'none' else None
		}
		if self.duration_value or (self.duration_unit != 'inst'): data["system"]["duration"] = {
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
		# data["system"]["consume"] = {}
		# data["system"]["ability"] = ''

		if self.action_type: data["system"]["actionType"] = self.action_type
		if self.attack_bonus: data["system"]["attack"] = { "bonus": self.attack_bonus }
		# data["system"]["chatFlavor"] = ''
		# data["system"]["critical"] = {
		# 	"threshold": None,
		# 	"damage": ""
		# }
		if self.damage["parts"] or self.damage["versatile"]:
			data["system"]["damage"] = {
				"parts": self.damage["parts"],
				"versatile": self.damage["versatile"]
			}
			if self.damage_bonus:
				if len(data["system"]["damage"]["parts"]): data["system"]["damage"]["parts"][0][0] += f' + {self.damage_bonus}'
				else: data["system"]["damage"]["parts"].append([f'{self.damage_bonus}', ''])
				if data["system"]["damage"]["versatile"]: data["system"]["damage"]["versatile"] += f' + {self.damage_bonus}'
		if self.formula: data["system"]["formula"] = self.formula
		if self.save: data["system"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": 'flat' if self.save_dc else 'none'
		}

		if self.modifiable_item: data["system"]["modify"] = self.modifiable_item

		if self.category != False:
			data["system"]["type"] = {
				"value": self.category,
				"subtype": self.subcategory,
				"baseItem": self.base_item.base_item if self.base_item else None
		}
		data["system"]["-=baseItem"] = None
		data["system"]["-=weaponType"] = None
		data["system"]["-=consumableType"] = None
		data["system"]["-=ammoType"] = None
		data["system"]["-=toolType"] = None
		if "armor" in data["system"]: data["system"]["armor"]["-=type"] = None

		self.applyDataAutoTarget(data)
		self.applyDataSubtype(data)

		#	data["system"]["recharge"] = ''

		return [data]

	def applyDataAutoTarget(self, data, burst_or_rapid=False):
		if self.getType() == 'Weapon':
			if 'smr' in self.properties and type(smr := self.properties["smr"].split(', ')) == list:
				mod = (int(smr[0]) - 10) // 2
				prof = int(smr[1])

				if burst_or_rapid:
					data["system"]["save"] = {
						"dc": 8 + mod + prof + self.attack_bonus,
						"scaling": 'flat'
					}
				else:
					data["system"]["attack"] = {
						"bonus": f'{mod} + {prof}',
						"flat": True
					}

				data["system"]["damage"]["parts"][0][0] = f'{self.base_item.raw_damageNumberOfDice}d{self.base_item.raw_damageDieType} + {mod}'

		return data

	def applyDataSubtype(self, data):
		if self.base_item:
			return data
		elif self.raw_type == 'AdventuringGear':
			data["system"]["armor"] = {
				"value": None,
				"dex": None,
			}
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
			data["system"]["armor"] = {
				"value": 2,
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

			data["system"]["-=modificationSlot"] = None

			# data["system"]["properties"]["indeterminate"] = { key: False for key in self.properties.keys() }
		else:
			raise ValueError(self.raw_name, self.raw_type)

		return data

	def getFile(self, importer):
		return f'Enhanced{self.raw_type}'
