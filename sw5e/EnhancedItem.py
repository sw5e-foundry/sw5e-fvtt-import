import sw5e.Entity, utils.text
import re, json, copy

class EnhancedItem(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.name = utils.text.clean(raw_item, "name")
		self.typeEnum = utils.text.raw(raw_item, "typeEnum")
		self.type = utils.text.clean(raw_item, "type")
		self.rarityOptionsEnum = utils.text.raw(raw_item, "rarityOptionsEnum")
		self.rarityOptions = utils.text.cleanJson(raw_item, "rarityOptions")
		self.rarityText = utils.text.clean(raw_item, "rarityText")
		self.searchableRarity = utils.text.clean(raw_item, "searchableRarity")
		self.requiresAttunement = utils.text.raw(raw_item, "requiresAttunement")
		self.valueText = utils.text.clean(raw_item, "valueText")
		self.text = utils.text.clean(raw_item, "text")
		self.hasPrerequisite = utils.text.raw(raw_item, "hasPrerequisite")
		self.prerequisite = utils.text.clean(raw_item, "prerequisite")
		self.subtype = utils.text.clean(raw_item, "subtype")

		self.subtypeType = \
			utils.text.clean(raw_item, utils.text.lowerCase(self.type)+'Type') or \
			utils.text.clean(raw_item, f'enhanced{self.type}Type') or 'None'
		self.subtypeTypeEnum = \
			utils.text.raw(raw_item, f'{utils.text.lowerCase(self.type)}TypeEnum') or \
			utils.text.raw(raw_item, f'enhanced{self.type}TypeEnum') or 0

		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_value, self.target_unit, self.target_type = self.getTarget()
		self.range_value, self.range_unit = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc = self.getAction()
		self.attack_bonus, self.damage_bonus = self.getAttackBonus()
		self.activation = self.getActivation()
		self.rarity = self.getRarity()

	def getActivation(self):
		return utils.text.getActivation(self.text, self.uses, self.recharge)

	def getDuration(self):
		return utils.text.getDuration(self.text, self.name)

	def getTarget(self):
		return utils.text.getTarget(self.text, self.name)

	def getRange(self):
		return utils.text.getRange(self.text, self.name)

	def getUses(self):
		return utils.text.getUses(self.text, self.name)

	def getAction(self):
		return utils.text.getAction(self.text, self.name)

	def getAttackBonus(self):
		if match := re.search(r'You (?:have|gain) a \+(?P<bonus>\d+) (?:bonus )?to (?P<attack>attack)?(?: and )?(?P<dmg>damage)? rolls (?:made )?with this', self.text):
			return match["bonus"] if match["attack"] else 0, match["bonus"] if match["dmg"] else 0
		return 0, 0

	def getRarity(self):
		mapping = {
			"standard": 'common',
			"premium": 'uncommon',
			"prototype": 'rare',
			"advanced": 'veryRare',
			"legendary": 'legendary',
			"artifact": 'artifact',
		}
		return mapping[self.rarityText]

	def applySubtype(self, data):
		if self.subtypeType == 'Specific': return data

		if self.type == 'AdventuringGear':
			data["data"]["armor"] = {
				"value": None,
				"dex": None,
			}
			if self.subtype in ('body', 'feet', 'hands', 'head', 'shoulders', 'waist', 'wrists', 'legs'):
				data["data"]["armor"]["type"] = 'clothing'
			elif self.subtype in (None, '', 'finger', 'other', 'neck', 'back', 'wrist'):
				data["data"]["armor"]["type"] = 'trinket'
			else:
				raise ValueError(self.name, self.type, self.subtype, self.subtypeType)
		elif self.type == 'Armor':
			if self.subtypeType in ('AnyHeavy', 'Any'):
				data["data"]["armor"] = {
					"value": 16,
					"type": 'heavy',
					"dex": 0,
				}
			elif self.subtypeType == 'AnyMedium':
				data["data"]["armor"] = {
					"value": 14,
					"type": 'medium',
					"dex": 2,
				}
			elif self.subtypeType == 'AnyLight':
				data["data"]["armor"] = {
					"value": 11,
					"type": 'light',
					"dex": None,
				}
			else:
				raise ValueError(self.name, self.type, self.subtype, self.subtypeType)
		elif self.type == 'Consumable':
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
			if mapping[self.subtypeTypeEnum] == 'CUSTOM':
				if self.subtype == 'substance':
					## TODO: Change to alcoholic beverage once that type exists
					data["data"]["consumableType"] = 'adrenal'
				elif self.subtype == 'ammunition':
					data["data"]["consumableType"] = 'ammo'
				elif self.subtype in ('technology', 'medpac'):
					data["data"]["consumableType"] = self.subtype
				else:
					raise ValueError(self.name, self.subtype, self.subtypeType)
			else:
				data["data"]["consumableType"] = mapping[self.subtypeTypeEnum]
		elif self.type == 'CyberneticAugmentation':
			## TODO: Change this once mods are supported
			pass
		elif self.type == 'DroidCustomization':
			## TODO: Change this once mods are supported
			pass
		elif self.type == 'Focus':
			data["data"]["armor"] = {
				"value": None,
				"type": 'trinket',
				"dex": None,
			}
			if self.subtype in ('force', 'focus'):
				data["data"]["armor"]["type"] = 'trinket'
			elif self.subtype == 'tech':
				data["data"]["armor"]["type"] = 'technology'
			else:
				raise ValueError(self.name, self.type, self.subtype, self.subtypeType)
		elif self.type == 'ItemModification':
			## TODO: Change this once mods are supported
			pass
		elif self.type == 'Shield':
			data["data"]["armor"] = {
				"value": 2,
				"type": 'shield',
				"dex": None,
			}
			if self.subtypeType == 'Light':
				data["data"]["armor"]["value"] = 1
			elif self.subtypeType in ('Medium', 'Any'):
				data["data"]["armor"]["value"] = 2
			elif self.subtypeType == 'Heavy':
				data["data"]["armor"]["value"] = 3
			else:
				raise ValueError(self.name, self.type, self.subtype, self.subtypeType)
		elif self.type == 'Weapon':
			if not data["data"]["activation"]["type"]:
				data["data"]["activation"] = { "type": 'action', "cost": 1 }
			if not data["data"]["target"]["type"]:
				data["data"]["target"] = { "value": 1, "type": 'enemy' }

			if self.subtypeType in ('AnyWithProperty', 'AnyBlasterWithProperty', 'AnyVibroweaponWithProperty', 'AnyLightweaponWithProperty'):
				print(f"	'{self.subtypeType}' enhanced weapon detected. This kind of item is not supported since there currently no examples to know what they should look like.")
				print(f'{self.name=}')
				print(f'{self.type=}')
				print(f'{self.subtype=}')
				print(f'{self.subtypeType=}')
				print(f'{self.text=}')

			if self.subtypeType in ('Any', 'AnyWithProperty'):
				if data["data"]["actionType"] == 'other':
					data["data"]["actionType"] = 'mwak'
				if ("weaponType" not in data["data"]) or (not data["data"]["weaponType"]):
					data["data"]["weaponType"] = 'improv'
			elif self.subtypeType in ('AnyBlaster', 'AnyBlasterWithProperty'):
				data["data"]["actionType"] = 'rwak'
				data["data"]["weaponType"] = 'simpleB'
			elif self.subtypeType in ('AnyVibroweapon', 'AnyVibroweaponWithProperty'):
				data["data"]["actionType"] = 'mwak'
				data["data"]["weaponType"] = 'simpleVW'
			elif self.subtypeType in ('AnyLightweapon', 'AnyLightweaponWithProperty'):
				data["data"]["actionType"] = 'mwak'
				data["data"]["weaponType"] = 'simpleLW'
			else:
				raise ValueError(self.name, self.type, self.subtype, self.subtypeType)
		elif self.type == 'Valuable':
			print("	'Valuable' enhanced item detected. This kind of item is not supported since there currently no examples to know what they should look like.")
			print(f'{self.name=}')
			print(f'{self.type=}')
			print(f'{self.subtype=}')
			print(f'{self.subtypeType=}')
			print(f'{self.text=}')
			pass
		elif self.type == 'ShipArmor':
			## TODO: change this one ships are supported
			pass
		elif self.type == 'ShipShield':
			## TODO: change this one ships are supported
			pass
		elif self.type == 'ShipWeapon':
			## TODO: change this one ships are supported
			pass
		elif self.type in ('BlasterModification', 'ClothingModification', 'WristpadModification', 'ArmorModification', 'VibroweaponModification', 'LightweaponModification', 'FocusGeneratorModification', ):
			## TODO: Change this once mods are supported
			pass
		else:
			raise ValueError(self.name, self.type)

		return data

	def getDescription(self, base_text = None):
		text = self.text

		header = ''
		if self.requiresAttunement:
			if text.startswith('_**Requires attunement'):
				match = re.search('\n', text)
				header, text = text[:match.end()], text[match.end():]
			else:
				header += f'_**Requires attunement**_\r\n'

		if self.prerequisite:
			header += f'_Prerequisite: {self.prerequisite}_\r\n'

		if header: header += '<hr/>\n'

		text = header + text

		text = utils.text.markdownToHtml(text)
		if base_text:
			base_text = utils.text.markdownToHtml(f'### {base_text[0]}') + '\n' + base_text[1]
			text = text + '\n<p>&nbsp;</p>\n' + base_text
		else:
			header = re.sub(r'([a-z])([A-Z])', r'\1 \2', self.type)
			header = f'##### {header}'
			if self.subtype and (not base_text):
				header += f' ({self.subtype.title()})'
			text = f'{utils.text.markdownToHtml(header)}\n {text}'
		return text

	def getImg(self):
		# TODO: Remove this once there are icons for Enhanced Items
		if self.name not in ('Alacrity Adrenal', 'Battle Adrenal', 'Stamina Adrenal', 'Strength Adrenal', 'Mandalorian Beskar\'gam', 'Mandalorian Helmet', 'Mandalorian Shuk\'orok'):
			return 'icons/svg/item-bag.svg'

		name = self.name
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Enhanced%20Items/{name}.webp'

	def getType(self):
		mapping = [
			None, ## 0 = Unknown
			'equipment', ## 1 = AdventuringGear
			'equipment', ## 2 = Armor
			'consumable', ## 3 = Consumable
			'loot', ## 4 = CyberneticAugmentation
			'loot', ## 5 = DroidCustomization
			'equipment', ## 6 = Focus
			'loot', ## 7 = ItemModification
			'equipment', ## 8 = Shield
			'weapon', ## 9 = Weapon
			None, ## 10 = ?
			'loot', ## 11 = ShipArmor
			'loot', ## 12 = ShipShield
			'loot', ## 13 = ShipWeapon
			'loot', ## 14 = BlasterModification
			'loot', ## 15 = ClothingModification
			'loot', ## 16 = WristpadModification
			'loot', ## 17 = ArmorModification
			'loot', ## 18 = VibroweaponModification
			'loot', ## 19 = LightweaponModification
			'loot', ## 20 = FocusGeneratorModification
		]
		item_type = mapping[self.typeEnum]
		return item_type or 'loot'

	def getData(self, importer):
		superdata = super().getData(importer)[0]

		data = superdata

		def choose(base, enhanced, field, default):
			if field in base and base[field] != default: return base[field]
			if enhanced != default: return enhanced
			return default

		if self.subtypeType == 'Specific':
			get_data = { 'name': self.subtype.title(), 'equipmentCategory': self.type.title() }
			base_item = importer.get(self.getType(), data=get_data)

			if base_item:
				data = base_item.getData(importer)

				for item in data:
					mode = (re.search(r'\.mode-(.*)', item["flags"]["uid"]) or [None,None])[1]

					for key in superdata:
						if key in ("data", "img"): continue
						item[key] = copy.deepcopy(superdata[key])

					if self.getImg() != 'icons/svg/item-bag.svg':
						item["img"] = self.getImg()

					if mode:
						item["name"] += f' ({mode.title()})'
						item["flags"]["uid"] += f'.mode-{mode}'

					item["data"]["description"] = {
						"value": self.getDescription(base_text = (base_item.name, item["data"]["description"]["value"]))
					}
					item["data"]["source"] = self.contentSource
					item["data"]["attunement"] = 1 if self.requiresAttunement else 0
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

					item["data"]["actionType"] = choose(item["data"], self.action_type, "actionType", 'other')
					item["data"]["attackBonus"] = self.attack_bonus
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

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["source"] = self.contentSource
		data["data"]["attunement"] = 1 if self.requiresAttunement else 0
		data["data"]["rarity"] = self.rarity

		data["data"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation != 'none' else None
		}
		data["data"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		data["data"]["target"] = {
			"value": self.target_value,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		data["data"]["range"] = {
			"value": self.range_value,
			"long": None,
			"units": self.range_unit
		}
		data["data"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}
		#	item["data"]["consume"] = {}
		#	item["data"]["ability"] = ''

		data["data"]["actionType"] = self.action_type
		data["data"]["attackBonus"] = self.attack_bonus
		#	item["data"]["chatFlavor"] = ''
		#	item["data"]["critical"] = None
		data["data"]["damage"] = {
			"parts": self.damage["parts"],
			"versatile": self.damage["versatile"]
		}
		data["data"]["formula"] = self.formula
		data["data"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": "flat" if self.save_dc else "power"
		}

		self.applySubtype(data)

		#	data["data"]["recharge"] = ''

		return [data]

	def getFile(self, importer):
		return f'Enhanced{self.type}'
