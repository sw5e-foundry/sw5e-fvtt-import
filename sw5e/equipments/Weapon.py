import sw5e.Equipment, utils.text
import re, json, copy

class Weapon(sw5e.Equipment.Equipment):
	weapon_properties = {
		"amm": 'Ammunition',
		"aut": 'Auto',
		"bur": 'Burst',
		"bru": 'Brutal',
		"con": 'Constitution',
		"def": 'Defensive',
		"dex": 'Dexterity',
		"dir": 'Dire',
		"drm": 'Disarming',
		"dgd": 'Disguised',
		"dis": 'Disintegrate',
		"dpt": 'Disruptive',
		"dou": 'Double',
		"exp": 'Explosive',
		"fin": 'Finesse',
		"fix": 'Fixed',
		"foc": 'Focus',
		"hvy": 'Heavy',
		"hid": 'Hidden',
		"hom": 'Homing',
		"ion": 'Ionizing',
		"ken": 'Keen',
		"lgt": 'Light',
		"lum": 'Luminous',
		"mlt": 'Melt',
		"mig": 'Mighty',
		"neu": 'Neuralizing',
		"ovr": 'Overheat',
		"pic": 'Piercing',
		"pow": 'Power',
		"ran": 'Range',
		"rap": 'Rapid',
		"rch": 'Reach',
		"rel": 'Reload',
		"ret": 'Returning',
		"sat": 'Saturate',
		"shk": 'Shocking',
		"sil": 'Silent',
		"son": 'Sonorous',
		"spc": 'Special',
		"str": 'Strength',
		"swi": 'Switch',
		"thr": 'Thrown',
		"two": 'Two-Handed',
		"ver": 'Versatile',
		"vic": 'Vicious',
		"zon": 'Zone',
	}

	def load(self, raw_item):
		super().load(raw_item)

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.activation = 'action'

		self.weapon_type = self.getWeaponType()
		self.ammo_type = self.getAmmoType()

	def getImg(self, importer=None):
		kwargs = {
			'item_type': self.weaponClassification,
			# 'no_img': ('Unknown',),
			'default_img': 'systems/sw5e/packs/Icons/Simple%20Blasters/Hold-out.webp',
			'plural': True
		}
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		properties = {prop: self.propertiesMap[prop] for prop in self.propertiesMap if prop != 'Special'}

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

		if 'Special' in self.propertiesMap:
			if text: text += '\n'
			text += utils.text.markdownToHtml('#### Special\n' + self.description)

		return text

	def getRange(self):
		short_range, long_range = None, None
		if rang := (utils.text.getProperty('Ammunition', self.propertiesMap) or utils.text.getProperty('Range', self.propertiesMap)):
			if rang == 'special': short_range = 'special'
			elif type(rang) == list: short_range, long_range = rang
			else: short_range = rang
		elif utils.text.getProperty('Reach', self.propertiesMap):
			short_range = 10
		return {
			'value': short_range,
			'long': long_range,
			'units': 'ft'
		}

	def getUses(self):
		if self.ammo_type and self.ammo_type != 'Power Cell':
			rload = utils.text.getProperty('Reload', self.propertiesMap)
			return {
				"value": rload,
				"max": rload,
				"per": 'charges'
			}
		return {}

	def getConsume(self):
		if self.ammo_type == 'Power Cell': return {
			"type": 'charges',
			"target": '',
			"amount": 480 // utils.text.getProperty('Reload', self.propertiesMap)
		}
		elif self.ammo_type: return {
			"type": 'ammo',
			"target": '',
			"amount": 1
		}
		return {}

	def getActionType(self):
		if self.weapon_type in ('simpleB', 'martialB'):
			return 'rwak'
		else:
			return 'mwak'

	def getDamage(self):
		if (not self.damageNumberOfDice) or (not self.damageDieType):
			return {}

		die = f'{self.damageNumberOfDice}d{self.damageDieType} + @mod'
		damage_type = self.damageType.lower() if self.damageType != 'Unknown' else ''
		versatile = utils.text.getProperty('Versatile', self.propertiesMap) or ''
		return {
			"parts": [[ die, damage_type ]],
			"versatile": f'{versatile} +  @mod' if versatile else ''
		}

	def getWeaponType(self):
		w_class = self.weaponClassification

		simple = w_class.startswith('Simple')
		martial = not simple and w_class.startswith('Martial')

		blaster = w_class.endswith('Blaster') or utils.text.getProperty('Ammunition', self.propertiesMap) or utils.text.getProperty('Reload', self.propertiesMap)
		vibro = (not blaster) and w_class.endswith('Vibroweapon')
		light = (not blaster) and (not vibro) and w_class.endswith('Lightweapon')

		if simple and blaster: return 'simpleB'
		if simple and vibro: return 'simpleVW'
		if simple and light: return 'simpleLW'
		if martial and blaster: return 'martialB'
		if martial and vibro: return 'martialVW'
		if martial and light: return 'martialLW'
		return 'natural'

		return weapon_types[self.weaponClassificationEnum]

	def getAmmoType(self):
		if not utils.text.getProperty('Reload', self.propertiesMap): return None
		if self.damageType in ('Energy', 'Ion', 'Acid', 'Fire', 'Sonic', 'Lightning'): return 'Power Cell'
		else: return 'Cartridge' #TODO: detect other types of ammo (flechete, missile...)

	def getProperties(self):
		props = {};

		pattern = r'^(?P<property>' + (r'|'.join(self.weapon_properties.values())).lower() + r')'

		for prop in self.propertiesMap.values():
			prop = prop.lower()
			if prop == 'special': continue


			if (name := re.search(pattern, prop)):
				name = name['property']
				key = [key for key in self.weapon_properties if self.weapon_properties[key].lower() == name][0]
				if (value := re.search(r'(\d*d\d+)|((?<!d)\d+(?!d))', prop)):
					if value[1]: props[key] = value[1]
					else: props[key] = int(value[2])
				else:
					props[key] = True
			else: raise ValueError(self.name, prop, pattern)
		return props

	def getAutoTargetData(self, data):
		if type(auto := utils.text.getProperty('Auto', self.propertiesMap)) == list:
			mod = (auto[0] - 10) // 2
			prof = auto[1]
			data["data"]["ability"] = 'str'
			data["data"]["attackBonus"] = f'{mod} - @abilities.str.mod + {prof} - @attributes.prof'
			data["data"]["damage"]["parts"][0][0] = f'{self.damageNumberOfDice}d{self.damageDieType} + {mod}'
			data["data"]["proficient"] = True
		return data

	def getItemVariations(self, original_data, importer):
		data = []

		if self.modes:
			# data.append(original_data)
			for mode in self.modes:
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
				wpn.ammo_type = wpn.getAmmoType()

				wpn_data = wpn.getData(importer)[0]
				wpn_data["name"] = f'{self.name} ({mode["Name"]})'
				wpn_data["flags"]["uid"] = f'{self.uid}.mode-{mode["Name"]}'
				data.append(wpn_data)
		else:
			if not (utils.text.getProperty('Auto', self.propertiesMap) == True): data.append(original_data)
			if burst := utils.text.getProperty('Burst', self.propertiesMap):
				burst_data = copy.deepcopy(original_data)
				burst_data["name"] = f'{self.name} (Burst)'

				burst_data["data"]["target"]["value"] = '10'
				burst_data["data"]["target"]["units"] = 'ft'
				burst_data["data"]["target"]["type"] = 'cube'
				if self.ammo_type:
					burst_data["data"]["consume"]["amount"] *= burst
					if self.ammo_type != 'Power Cell':
						burst_data["data"]["uses"]["value"] //= burst
						burst_data["data"]["uses"]["max"] //= burst

				burst_data["data"]["actionType"] = 'save'
				burst_data["data"]["save"] = {
					"ability": 'dex',
					"dc": None,
					"scaling": 'dex'
				}
				burst_data["flags"]["uid"] = f'{self.uid}.mode-burst'
				data.append(burst_data)
			if rapid := utils.text.getProperty('Rapid', self.propertiesMap):
				rapid_data = copy.deepcopy(original_data)
				rapid_data["name"] = f'{self.name} (Rapid)'

				if self.ammo_type:
					rapid_data["data"]["consume"]["amount"] *= rapid
					if self.ammo_type != 'Power Cell':
						rapid_data["data"]["uses"]["value"] //= rapid
						rapid_data["data"]["uses"]["max"] //= rapid

				rapid_data["data"]["actionType"] = 'save'
				rapid_data["data"]["damage"]["parts"][0][0] = re.sub(r'^(\d+)d', lambda m: f'{int(m[1])*2}d', rapid_data["data"]["damage"]["parts"][0][0])
				rapid_data["data"]["save"] = {
					"ability": 'dex',
					"dc": None,
					"scaling": 'dex'
				}
				rapid_data["flags"]["uid"] = f'{self.uid}.mode-rapid'
				data.append(rapid_data)

		return data

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["target"]["value"] = 1
		data["data"]["target"]["width"] = None
		data["data"]["target"]["units"] = ''
		data["data"]["target"]["type"] = 'enemy'

		data["data"]["range"] = self.getRange()
		data["data"]["uses"] = self.getUses()
		data["data"]["consume"] = self.getConsume()
		data["data"]["actionType"] = self.getActionType()
		data["data"]["damage"] = self.getDamage()
		data["data"]["weaponType"] = self.weapon_type
		data["data"]["properties"] = self.getProperties()

		data = self.getAutoTargetData(data)
		return self.getItemVariations(data, importer)

	def getFile(self, importer):
		return self.weaponClassification
