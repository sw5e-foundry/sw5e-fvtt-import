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

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_unit, self.target_type = self.getTarget()
		self.range_value, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction()
		self.attack_bonus, self.damage_bonus = self.getAttackBonus()
		self.activation = self.getActivation()
		self.rarity = self.getRarity()
		self.modificationItemType = self.getModificationItemType()
		self.p_properties = self.getProperties()

		self.is_modification = self.raw_type.endswith('Modification') or self.raw_type in ('CyberneticAugmentation', 'DroidCustomization')

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
		target_type = self.modificationItemType or self.getType()

		if target_type == 'equipment':
			if self.raw_type == 'Focus': properties_list = utils.config.casting_properties
			else: properties_list = utils.config.armor_properties
		elif target_type == 'weapon':
			properties_list = utils.config.weapon_properties
		else:
			return {}

		return utils.text.getProperties(self.raw_text, properties_list, needs_end=True)

	def applySubtype(self, data):
		if self.raw_subtypeType == 'Specific': return data

		if self.raw_type == 'AdventuringGear':
			data["data"]["armor"] = {
				"value": None,
				"dex": None,
			}
			if self.raw_subtype in ('body', 'feet', 'hands', 'head', 'shoulders', 'waist', 'wrists', 'forearms', 'forearm', 'legs'):
				data["data"]["armor"]["type"] = 'clothing'
			elif self.raw_subtype in (None, '', 'finger', 'other', 'neck', 'back', 'wrist'):
				data["data"]["armor"]["type"] = 'trinket'
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Armor':
			if self.raw_subtypeType in ('AnyHeavy', 'Any'):
				data["data"]["armor"] = {
					"value": 16,
					"type": 'heavy',
					"dex": 0,
				}
			elif self.raw_subtypeType == 'AnyMedium':
				data["data"]["armor"] = {
					"value": 14,
					"type": 'medium',
					"dex": 2,
				}
			elif self.raw_subtypeType == 'AnyLight':
				data["data"]["armor"] = {
					"value": 11,
					"type": 'light',
					"dex": None,
				}
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Consumable':
			mapping = [
				None, ## None
				'adrenal', ## Adrenals
				'explosive', ## Explosives
				'poison', ## Poisons
				## Change to stimpac once that type exists
				'adrenal', ## Stimpacs
				'CUSTOM', ## Other
				'technology', ## Barriers
			]
			if mapping[self.raw_subtypeTypeEnum] == 'CUSTOM':
				if self.raw_subtype == 'substance':
					## TODO: Change to alcoholic beverage once that type exists
					data["data"]["consumableType"] = 'adrenal'
				elif self.raw_subtype == 'ammunition':
					data["data"]["consumableType"] = 'ammo'
					ammo_types = utils.config.ammo_types
					name = self.raw_name.lower()
					for ammo in ammo_types:
						amn = ammo["name"].lower()
						if name.find(amn) != -1:
							data["data"]["ammoType"] = ammo["id"]
							break
					if not 'ammoType' in data["data"]:
						desc = (self.raw_text or '').lower()
						for ammo in ammo_types:
							amn = ammo["name"].lower()
							if desc.find(amn) != -1:
								data["data"]["ammoType"] = ammo["id"]
								break
				elif self.raw_subtype in ('technology', 'medpac'):
					data["data"]["consumableType"] = self.raw_subtype
				else:
					raise ValueError(self.raw_name, self.raw_subtype, self.raw_subtypeType)
			else:
				data["data"]["consumableType"] = mapping[self.raw_subtypeTypeEnum]
		elif self.raw_type == 'CyberneticAugmentation':
			data["data"]["modificationType"] = 'cybernetic'
		elif self.raw_type == 'DroidCustomization':
			data["data"]["modificationType"] = 'droidcustomization'
		elif self.raw_type == 'Focus':
			data["data"]["armor"] = {
				"value": None,
				"type": 'trinket',
				"dex": None,
			}
			if self.raw_subtype in ('force', 'focus'):
				data["data"]["armor"]["type"] = 'focusgenerator'
				data["data"]["baseItem"] = 'focusgenerator'
			elif self.raw_subtype == 'tech':
				data["data"]["armor"]["type"] = 'wristpad'
				data["data"]["baseItem"] = 'wristpad'
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Shield':
			data["data"]["armor"] = {
				"value": 2,
				"type": 'shield',
				"dex": None,
			}
			if self.raw_subtypeType == 'Light':
				data["data"]["armor"]["value"] = 1
			elif self.raw_subtypeType in ('Medium', 'Any'):
				data["data"]["armor"]["value"] = 2
			elif self.raw_subtypeType == 'Heavy':
				data["data"]["armor"]["value"] = 3
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Weapon':
			if not utils.object.getProperty(data, 'data.activation.type'):
				utils.object.setProperty(data, 'data.activation', { "type": 'action', "cost": 1 }, force=True)
			if not utils.object.getProperty(data, 'data.target.type'):
				utils.object.setProperty(data, 'data.target', { "type": 'enemy', "value": 1 }, force=True)

			if self.raw_subtypeType in ('AnyWithProperty', 'AnyBlasterWithProperty', 'AnyVibroweaponWithProperty', 'AnyLightweaponWithProperty'):
				print(f"	'{self.raw_subtypeType}' enhanced weapon detected. This kind of item is not supported since there currently no examples to know what they should look like.")
				print(f'{self.raw_name=}')
				print(f'{self.raw_type=}')
				print(f'{self.raw_subtype=}')
				print(f'{self.raw_subtypeType=}')
				print(f'{self.raw_text=}')

			if self.raw_subtypeType in ('Any', 'AnyWithProperty'):
				if data["data"]["actionType"] == 'other':
					data["data"]["actionType"] = 'mwak'
				if ("weaponType" not in data["data"]) or (not data["data"]["weaponType"]):
					data["data"]["weaponType"] = 'improv'
			elif self.raw_subtypeType in ('AnyBlaster', 'AnyBlasterWithProperty'):
				data["data"]["actionType"] = 'rwak'
				data["data"]["weaponType"] = 'simpleB'
			elif self.raw_subtypeType in ('AnyVibroweapon', 'AnyVibroweaponWithProperty'):
				data["data"]["actionType"] = 'mwak'
				data["data"]["weaponType"] = 'simpleVW'
			elif self.raw_subtypeType in ('AnyLightweapon', 'AnyLightweaponWithProperty'):
				data["data"]["actionType"] = 'mwak'
				data["data"]["weaponType"] = 'simpleLW'
			else:
				raise ValueError(self.raw_name, self.raw_type, self.raw_subtype, self.raw_subtypeType)
		elif self.raw_type == 'Valuable':
			print("	'Valuable' enhanced item detected. This kind of item is not supported since there currently no examples to know what they should look like.")
			print(f'{self.raw_name=}')
			print(f'{self.raw_type=}')
			print(f'{self.raw_subtype=}')
			print(f'{self.raw_subtypeType=}')
			print(f'{self.raw_text=}')
			pass
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
			data["data"]["modificationItemType"] = self.modificationItemType

			data["data"]["modificationType"] = self.raw_subtype
			data["data"]["-=modificationSlot"] = None

			data["data"]["properties"]["indeterminate"] = { key: False for key in self.p_properties.keys() }
		else:
			raise ValueError(self.raw_name, self.raw_type)

		return data

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
			base_text = utils.text.markdownToHtml(f'### {base_text[0]}') + '\n' + base_text[1]
			text = text + '\n<p>&nbsp;</p>\n' + base_text
		else:
			header = re.sub(r'([a-z])([A-Z])', r'\1 \2', self.raw_type)
			header = f'##### {header}'
			if self.raw_subtype and (not base_text):
				header += f' ({self.raw_subtype.title()})'
			text = f'{utils.text.markdownToHtml(header)}\n {text}'
		return text

	def getImg(self, importer=None):
		# Try to find the base item and use it's item
		name = re.sub(r'\s*\([^()]*\)$', '', self.raw_name)
		name = re.sub(r'\s*Mk \w+$', '', name)
		if name != self.raw_name and (not self.is_modification):
			data = {
				'name': name,
				'equipment_type': self.getType().capitalize(),
				'equipmentCategory': self.raw_subtype
			}
			if importer and (base := importer.get('equipment', data=data)):
				return base.getImg(importer=importer)

		# TODO: Remove this once there are icons for Enhanced Items
		if name in utils.config.enhanced_item_icons['multi']:
			name = utils.text.slugify(name)
			if self.raw_searchableRarity != 'Standard': name = name + self.raw_searchableRarity
			return f'systems/sw5e/packs/Icons/Enhanced%20Items/{name}.webp'
		if name in utils.config.enhanced_item_icons['single']:
			name = utils.text.slugify(name)
			return f'systems/sw5e/packs/Icons/Enhanced%20Items/{name}.webp'

		# Use the modification subtype icons
		if self.is_modification:
			subtype = self.raw_subtype
			if self.raw_type == 'CyberneticAugmentation': subtype = f'cybernetic-{self.raw_subtype}'
			elif self.raw_type == 'DroidCustomization': subtype = f'droid-{self.raw_subtype}'
			return f'systems/sw5e/packs/Icons/Modifications/{subtype}.svg'

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

	def getAutoTargetData(self, data, base_item):
		if 'smr' in self.p_properties and type(auto := self.p_properties["smr"].split(', ')) == list:
			mod = (int(auto[0]) - 10) // 2
			prof = int(auto[1])
			data["data"]["ability"] = 'str'
			data["data"]["attackBonus"] = f'{mod} - @abilities.str.mod + {prof} - @attributes.prof'
			data["data"]["damage"]["parts"][0][0] = f'{base_item.raw_damageNumberOfDice}d{base_item.raw_damageDieType} + {mod}'
			data["data"]["proficient"] = True
		return data

	def getDataSpecific(self, importer, base_item):
		def choose(base, enhanced, field, default):
			if field in base and base[field] != default: return base[field]
			if enhanced != default: return enhanced
			return default

		superdata = super().getData(importer)[0]
		data = base_item.getData(importer)

		for item in data:
			mode = (re.search(r'\.mode-(.*)', item["flags"]["sw5e-importer"]["uid"]) or [None,None])[1]

			for key in superdata:
				if key in ("data", "img"): continue
				item[key] = copy.deepcopy(superdata[key])

			if self.getImg(importer=importer) != 'icons/svg/item-bag.svg':
				item["img"] = self.getImg(importer=importer)

			if mode:
				item["name"] += f' ({mode.title()})'
				item["flags"]["sw5e-importer"]["uid"] += f'.mode-{mode}'

			item["data"]["description"] = {
				"value": self.getDescription(base_text = (base_item.name, item["data"]["description"]["value"]))
			}
			item["data"]["source"] = self.raw_contentSource
			item["data"]["attunement"] = 1 if self.raw_requiresAttunement else 0
			item["data"]["rarity"] = self.rarity

			activation = choose(item["data"]["activation"], self.activation, "type", 'none')
			item["data"]["activation"] = {
				"type": activation,
				"cost": 1 if activation != 'none' else None
			}
			item["data"]["duration"] = {
				"value": choose(item["data"]["duration"], self.duration_value, "value", None),
				"units": choose(item["data"]["duration"], self.duration_unit, "units", 'inst'),
			}
			item["data"]["target"] = {
				"value": choose(item["data"]["target"], self.target_value, "value", None),
				"width": None,
				"units": choose(item["data"]["target"], self.target_unit, "units", ''),
				"type": choose(item["data"]["target"], self.target_type, "type", ''),
			}
			item["data"]["range"] = {
				"value": choose(item["data"]["range"], self.range_value, "value", None),
				"long": choose(item["data"]["range"], None, "long", None),
				"units": choose(item["data"]["range"], self.range_unit, "units", ''),
			}
			if "per" not in item["data"]["uses"] or item["data"]["uses"]["per"] == None:
				item["data"]["uses"] = {
					"value": None,
					"max": self.uses,
					"per": self.recharge
				}
			#	item["data"]["consume"] = {}
			#	item["data"]["ability"] = ''

			item["data"]["properties"] = {**item["data"]["properties"], **self.p_properties}
			item = self.getAutoTargetData(item, base_item);

			item["data"]["actionType"] = choose(item["data"], self.action_type, "actionType", 'other')
			if self.attack_bonus:
				if item["data"]["attackBonus"]: item["data"]["attackBonus"] += f' + {self.attack_bonus}'
				else: item["data"]["attackBonus"] = self.attack_bonus
			#	item["data"]["chatFlavor"] = ''
			#	item["data"]["critical"] = None
			item["data"]["damage"] = {
				"parts": (item["data"]["damage"]["parts"] if "parts" in item["data"]["damage"] else []) + self.damage["parts"],
				"versatile": choose(item["data"]["damage"], self.damage["versatile"], "versatile", '')
			}

			if self.damage_bonus and item["data"]["damage"]["parts"]:
				item["data"]["damage"]["parts"][0][0] += f' + {self.damage_bonus}'
				if item["data"]["damage"]["versatile"]: item["data"]["damage"]["versatile"] += f' + {self.damage_bonus}'

			item["data"]["formula"] = choose(item["data"], self.formula, "formula", '')
			item["data"]["save"] = {
				"ability": choose(item["data"]["save"], self.save, "ability", ''),
				"dc": None,
				"scaling": "none"
			}

			item = self.applySubtype(item)

			#	item["data"]["recharge"] = ''

		return data

	def getData(self, importer):
		if (not self.is_modification) and self.raw_subtypeType == 'Specific':
			get_data = { 'name': self.raw_subtype.title(), 'equipmentCategory': self.raw_type.title() }
			base_item = importer.get(self.getType(), data=get_data)

			if base_item: return self.getDataSpecific(importer, base_item)

		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["source"] = self.raw_contentSource
		data["data"]["attunement"] = 1 if self.raw_requiresAttunement else 0
		data["data"]["rarity"] = self.rarity

		if self.activation: data["data"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation != 'none' else None
		}
		if self.duration_value or self.duration_unit: data["data"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		if self.target_value or self.target_unit or self.target_type: data["data"]["target"] = {
			"value": self.target_value,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		if self.range_value or self.range_unit: data["data"]["range"] = {
			"value": self.range_value,
			"long": None,
			"units": self.range_unit
		}
		if self.uses or self.recharge: data["data"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}
		#	item["data"]["consume"] = {}
		#	item["data"]["ability"] = ''

		if self.action_type: data["data"]["actionType"] = self.action_type
		if self.attack_bonus: data["data"]["attackBonus"] = self.attack_bonus
		if self.damage_bonus: data["data"]["damageBonus"] = self.damage_bonus
		#	item["data"]["chatFlavor"] = ''
		data["data"]["critical"] = {
			"threshold": None,
			"damage": ""
		}
		if self.damage: data["data"]["damage"] = {
			"parts": self.damage["parts"],
			"versatile": self.damage["versatile"]
		}
		if self.formula: data["data"]["formula"] = self.formula
		if self.save: data["data"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": "flat" if self.save_dc else "power"
		}

		data["data"]["properties"] = self.p_properties

		self.applySubtype(data)

		#	data["data"]["recharge"] = ''

		return [data]

	def getFile(self, importer):
		return f'Enhanced{self.raw_type}'
