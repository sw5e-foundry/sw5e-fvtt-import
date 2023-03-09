import sw5e.Equipment, utils.text
import re, json, copy

class Weapon(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.activation = 'action'

		self.weapon_type = self.getWeaponType()
		self.ammo_types = self.getAmmoTypes()
		self.p_properties = self.getProperties()

	def getImg(self, importer=None):
		kwargs = {
			'item_type': self.raw_weaponClassification,
			# 'no_img': ('Unknown',),
			'default_img': 'systems/sw5e/packs/Icons/Simple%20Blasters/Hold-out.webp',
			'plural': True
		}
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		properties = {prop: self.raw_propertiesMap[prop] for prop in self.raw_propertiesMap if prop != 'Special'}

		text = ''

		if importer:
			def getContent(prop_name):
				prop = importer.get('weaponProperty', data={'name': prop_name})
				if prop: return prop.getContent(val=properties[prop_name])
				else: return properties[prop_name].capitalize()
			text = '\n'.join([getContent(prop) for prop in properties])
		else:
			text = ', '.join([properties[prop].capitalize() for prop in properties if prop != 'Ammunition'])
			text = utils.text.markdownToHtml(text)

		if 'Special' in self.raw_propertiesMap:
			if text: text += '\n'
			if (special := self.raw_propertiesMap["Special"]).lower() != "special":
				text += utils.text.markdownToHtml('#### Special\n' + special)
			elif self.raw_description:
				text += utils.text.markdownToHtml('#### Special\n' + self.raw_description)
			else:
				raise ValueError

		return text

	def getRange(self):
		short_range, long_range = None, None
		if rang := (utils.text.getProperty('Ammunition', self.raw_propertiesMap) or utils.text.getProperty('Range', self.raw_propertiesMap)):
			if rang == 'special': short_range = 'special'
			elif type(rang) == list: short_range, long_range = rang
			else: short_range = rang
		elif utils.text.getProperty('Reach', self.raw_propertiesMap):
			short_range = 10
		return {
			'value': short_range,
			'long': long_range,
			'units': 'ft'
		}

	def getActionType(self):
		if self.weapon_type in ('simpleB', 'martialB'):
			return 'rwak'
		else:
			return 'mwak'

	def getDamage(self):
		if (not self.raw_damageNumberOfDice) or (not self.raw_damageDieType):
			return {}

		die = self.raw_damageNumberOfDice
		if self.raw_damageDieType == -1:
			_, damage, _, _, _, _ = utils.text.getAction(self.raw_description, self.name)
			die = damage["parts"][0][0]
		elif self.raw_damageDieType > 1:
			die = f'{die}d{self.raw_damageDieType}'
		elif self.raw_damageDieType != 1:
			raise ValueError
		die = f'{die} + @mod'

		damage_type = self.raw_damageType.lower() if self.raw_damageType != 'Unknown' else ''
		versatile = utils.text.getProperty('Versatile', self.raw_propertiesMap) or ''
		return {
			"parts": [[ die, damage_type ]],
			"versatile": f'{versatile} +  @mod' if versatile else ''
		}

	def getWeaponType(self):
		w_class = self.raw_weaponClassification

		simple = w_class.startswith('Simple')
		martial = w_class.startswith('Martial')
		exotic = w_class.startswith('Exotic')

		blaster = w_class.endswith('Blaster') or utils.text.getProperty('Ammunition', self.raw_propertiesMap) or utils.text.getProperty('Reload', self.raw_propertiesMap)
		vibro = (not blaster) and w_class.endswith('Vibroweapon')
		light = (not blaster) and (not vibro) and w_class.endswith('Lightweapon')

		if simple and blaster: return 'simpleB'
		if simple and vibro: return 'simpleVW'
		if simple and light: return 'simpleLW'
		if martial and blaster: return 'martialB'
		if martial and vibro: return 'martialVW'
		if martial and light: return 'martialLW'
		if exotic and blaster: return 'exoticB'
		if exotic and vibro: return 'exoticVW'
		if exotic and light: return 'exoticLW'
		return 'natural'

		return weapon_types[self.raw_weaponClassificationEnum]

	def getAmmoTypes(self):
		if (self.name == "Rotary Cannon"): return ['powerGenerator']
		elif (self.name == "Flechette Cannon"): return ['flechetteMag']
		elif (self.name == "Vapor Projector"): return ['projectorTank']
		elif (self.name == "Wrist launcher"): return ['dart', 'flechetteClip', 'missile', 'projectorCanister', 'snare']
		elif (self.name == "Bolt-thrower"): return ['bolt']
		elif (self.name in ["Shortbow", "Compound bow"]): return ['arrow']
		elif (self.name.endswith("launcher")): return [self.name.split()[0].lower()]
		elif not utils.text.getProperty('Reload', self.raw_propertiesMap): return []
		elif self.raw_damageType == "Kinetic": return ['cartridge']
		else: return ['powerCell']

	def getPropertiesList(self):
		return utils.config.weapon_properties

	def getProperties(self):
		properties_list = self.getPropertiesList()

		properties = {
			**utils.text.getProperties(self.raw_propertiesMap.values(), properties_list, error=True),
			**utils.text.getProperties(self.raw_description, properties_list),
		}

		return properties

	def getAutoTargetData(self, data):
		if 'smr' in self.p_properties and type(smr := self.p_properties["smr"].split('/')) == list:
			mod = (int(smr[0]) - 10) // 2
			prof = int(smr[1])
			data["data"]["ability"] = 'str'
			data["data"]["attackBonus"] = f'{mod} - @abilities.str.mod + {prof} - @attributes.prof'
			data["data"]["damage"]["parts"][0][0] = f'{self.raw_damageNumberOfDice}d{self.raw_damageDieType} + {mod}'
			data["data"]["proficient"] = True
		return data

	def getItemVariations(self, original_data, importer):
		data = []

		if self.raw_modes:
			# data.append(original_data)
			for mode in self.raw_modes:
				wpn = copy.deepcopy(self)
				wpn.modes = []

				no = ([], {}, (), 0, '0', None, 'None', 'none', 'Unknown', 'unknown')

				if (var := utils.text.clean(mode, "Description")) not in no: wpn.description = var
				if (var := utils.text.raw(mode, "Cost")) not in no: wpn.cost = var
				if (var := utils.text.clean(mode, "Weight")) not in no: wpn.weight = var
				if (var := utils.text.raw(mode, "EquipmentCategoryEnum")) not in no: wpn.equipmentCategoryEnum = var
				if (var := utils.text.clean(mode, "EquipmentCategory")) not in no: wpn.equipmentCategory = var
				if (var := utils.text.raw(mode, "DamageNumberOfDice")) not in no: wpn.damageNumberOfDice = var
				if (var := utils.text.raw(mode, "DamageTypeEnum")) not in no: wpn.damageTypeEnum = var
				if (var := utils.text.clean(mode, "DamageType")) not in no: wpn.damageType = var
				if (var := utils.text.raw(mode, "DamageDieModifier")) not in no: wpn.damageDieModifier = var
				if (var := utils.text.raw(mode, "WeaponClassificationEnum")) not in no: wpn.weaponClassificationEnum = var
				if (var := utils.text.clean(mode, "WeaponClassification")) not in no: wpn.weaponClassification = var
				if (var := utils.text.raw(mode, "ArmorClassificationEnum")) not in no: wpn.armorClassificationEnum = var
				if (var := utils.text.clean(mode, "ArmorClassification")) not in no: wpn.armorClassification = var
				if (var := utils.text.raw(mode, "DamageDiceDieTypeEnum")) not in no: wpn.damageDiceDieTypeEnum = var
				if (var := utils.text.raw(mode, "DamageDieType")) not in no: wpn.damageDieType = var
				if (var := utils.text.cleanJson(mode, "Properties")) not in no: wpn.properties += var
				if (var := utils.text.cleanJson(mode, "PropertiesMap")) not in no: wpn.propertiesMap.update(var)

				wpn.weapon_type = wpn.getWeaponType()
				wpn.ammo_types = wpn.getAmmoTypes()

				wpn_data = wpn.getData(importer)[0]
				wpn_data["name"] = f'{self.name} ({mode["Name"]})'
				wpn_data["flags"]["sw5e-importer"]["uid"] = f'{self.uid}.mode-{mode["Name"]}'
				data.append(wpn_data)
		else:
			if not (utils.text.getProperty('Auto', self.raw_propertiesMap) == True): data.append(original_data)
			if burst := utils.text.getProperty('Burst', self.raw_propertiesMap):
				burst_data = copy.deepcopy(original_data)
				burst_data["name"] = f'{self.name} (Burst)'

				burst_data["data"]["target"]["value"] = '10'
				burst_data["data"]["target"]["units"] = 'ft'
				burst_data["data"]["target"]["type"] = 'cube'

				burst_data["data"]["actionType"] = 'save'
				burst_data["data"]["save"] = {
					"ability": 'dex',
					"dc": None,
					"scaling": 'dex'
				}
				burst_data["flags"]["sw5e-importer"]["uid"] = f'{self.uid}.mode-burst'
				data.append(burst_data)
			if rapid := utils.text.getProperty('Rapid', self.raw_propertiesMap):
				rapid_data = copy.deepcopy(original_data)
				rapid_data["name"] = f'{self.name} (Rapid)'

				rapid_data["data"]["actionType"] = 'save'
				rapid_data["data"]["damage"]["parts"][0][0] = re.sub(r'^(\d+)d', lambda m: f'{int(m[1])*2}d', rapid_data["data"]["damage"]["parts"][0][0])
				rapid_data["data"]["save"] = {
					"ability": 'dex',
					"dc": None,
					"scaling": 'dex'
				}
				rapid_data["flags"]["sw5e-importer"]["uid"] = f'{self.uid}.mode-rapid'
				data.append(rapid_data)

		return data

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["target"]["value"] = 1
		data["data"]["target"]["width"] = None
		data["data"]["target"]["units"] = ''
		data["data"]["target"]["type"] = 'enemy'

		data["data"]["range"] = self.getRange()
		data["data"]["actionType"] = self.getActionType()
		data["data"]["damage"] = self.getDamage()
		data["data"]["weaponType"] = self.weapon_type
		data["data"]["properties"] = self.p_properties
		data["data"]["properties"]["-=amm"] = None
		data["data"]["critical"] = {
			"threshold": None,
			"damage": ""
		}

		data["data"]["ammo"] = { "types": self.ammo_types }
		data["data"]["consume"] = { "type": "", "target": "", "ammount": None }

		data = self.getAutoTargetData(data)
		return self.getItemVariations(data, importer)

	def getFile(self, importer):
		return self.raw_weaponClassification
