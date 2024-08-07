import sw5e.Equipment, utils.config, utils.object, utils.text
import re, json, copy

class Weapon(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.weapon_class = self.getWeaponClass()
		self.ammo_types = self.getAmmoTypes()

	def getActivation(self):
		return 'action'

	def getTarget(self):
		return 1, None, '', 'enemy'

	def getRange(self):
		short_range, long_range = None, None
		if rang := (utils.text.getProperty('Ammunition', self.raw_propertiesMap) or utils.text.getProperty('Range', self.raw_propertiesMap)):
			if rang == 'special': pass
			elif type(rang) == list: short_range, long_range = rang
			else: short_range = int(rang)
		elif utils.text.getProperty('Reach', self.raw_propertiesMap):
			short_range = 10
		return short_range, long_range, 'ft'

	def getAction(self):
		return self.getActionType(), self.getDamage(), None, None, None, None

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

	def getActionType(self):
		if self.category in ('simpleB', 'martialB'):
			return 'rwak'
		else:
			return 'mwak'

	def getDamage(self):
		if (not self.raw_damageNumberOfDice) or (not self.raw_damageDieType):
			return {}

		die = self.raw_damageNumberOfDice
		if self.raw_damageDieType == -1:
			_, damage, other_formula, _, _, _ = utils.text.getAction(self.raw_description, self.name)
			die = other_formula or damage["parts"][0][0]
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

	def getEquipmentCategory(self):
		wc = self.raw_weaponClassification

		start = ''
		for training in ('Simple', 'Martial', 'Exotic'):
			if wc.startswith(training): start = training.lower()

		if wc.endswith('Blaster') or self.getProperty('Ammunition') or self.getProperty('Reload'):
			return f'{start}B'
		for mode in ('Vibroweapon', 'Lightweapon'):
			if wc.endswith(mode): return f'{start}{mode[0]}W'

		if wc == 'Natural': return 'natural'

		return 'improv'

	def getWeaponClass(self):
		if self.category == 'natural' or self.raw_fakeItem: return ''
		for (classification, wpns) in utils.config.weapon_classes.items():
			if self.name.lower() in wpns:
				return classification
		else: raise ValueError(self.name)

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

		return utils.object.applyType(properties, properties_list)

	def getAutoTargetData(self, data, burst_or_rapid=False):
		if 'smr' in self.p_properties and type(smr := self.p_properties["smr"].split('/')) == list:
			mod = (int(smr[0]) - 10) // 2
			prof = int(smr[1])

			if burst_or_rapid:
				data["system"]["save"] = {
					"dc": 8 + mod + prof,
					"scaling": 'flat'
				}
			else:
				data["system"]["attack"] = {
					"bonus": f'{mod} + {prof}',
					"flat": True
				}

			data["system"]["damage"]["parts"][0][0] = f'{self.raw_damageNumberOfDice}d{self.raw_damageDieType} + {mod}'
		return data

	def getItemVariations(self, original_data, importer):
		data = []

		if self.raw_modes:
			# data.append(original_data)
			for mode in self.raw_modes:
				wpn = copy.deepcopy(self)
				wpn.raw_modes = []

				no = ([], {}, (), 0, '0', None, 'None', 'none', 'Unknown', 'unknown')

				if (var := utils.text.clean(mode, "Description")) not in no: wpn.raw_description = var
				if (var := utils.text.raw(mode, "Cost")) not in no: wpn.raw_cost = var
				if (var := utils.text.clean(mode, "Weight")) not in no: wpn.raw_weight = var
				if (var := utils.text.raw(mode, "EquipmentCategoryEnum")) not in no: wpn.raw_equipmentCategoryEnum = var
				if (var := utils.text.clean(mode, "EquipmentCategory")) not in no: wpn.raw_equipmentCategory = var
				if (var := utils.text.raw(mode, "DamageNumberOfDice")) not in no: wpn.raw_damageNumberOfDice = var
				if (var := utils.text.raw(mode, "DamageTypeEnum")) not in no: wpn.raw_damageTypeEnum = var
				if (var := utils.text.clean(mode, "DamageType")) not in no: wpn.raw_damageType = var
				if (var := utils.text.raw(mode, "DamageDieModifier")) not in no: wpn.raw_damageDieModifier = var
				if (var := utils.text.raw(mode, "WeaponClassificationEnum")) not in no: wpn.raw_weaponClassificationEnum = var
				if (var := utils.text.clean(mode, "WeaponClassification")) not in no: wpn.raw_weaponClassification = var
				if (var := utils.text.raw(mode, "ArmorClassificationEnum")) not in no: wpn.raw_armorClassificationEnum = var
				if (var := utils.text.clean(mode, "ArmorClassification")) not in no: wpn.raw_armorClassification = var
				if (var := utils.text.raw(mode, "DamageDiceDieTypeEnum")) not in no: wpn.raw_damageDiceDieTypeEnum = var
				if (var := utils.text.raw(mode, "DamageDieType")) not in no: wpn.raw_damageDieType = var
				if (var := utils.text.cleanJson(mode, "Properties")) not in no: wpn.raw_properties += var
				if (var := utils.text.cleanJson(mode, "PropertiesMap")) not in no: wpn.raw_propertiesMap.update(var)

				wpn.category = wpn.getEquipmentCategory()
				wpn.subcategory = wpn.getEquipmentSubcategory()
				wpn.ammo_types = wpn.getAmmoTypes()

				wpn_data = wpn.getData(importer)[0]
				wpn_data["name"] = f'{self.name} ({mode["Name"]})'
				wpn_data["flags"]["sw5e-importer"]["uid"] = f'{self.uid}.mode-{mode["Name"]}'
				data.append(wpn_data)
		else:
			if not (utils.text.getProperty('Auto', self.raw_propertiesMap) == True):
				normal_data = copy.deepcopy(original_data)
				normal_data = self.getAutoTargetData(normal_data)
				data.append(normal_data)
			if burst := utils.text.getProperty('Burst', self.raw_propertiesMap):
				burst_data = copy.deepcopy(original_data)
				burst_data["name"] = f'{self.name} (Burst)'

				burst_data["system"]["target"] = {
					"value": 10,
					"units": 'ft',
					"type": 'cube',
				}
				burst_data["system"]["actionType"] = 'save'
				burst_data["system"]["save"] = {
					"ability": 'dex',
					"dc": None,
					"scaling": 'dex'
				}
				burst_data["flags"]["sw5e-importer"]["uid"] = f'{self.uid}.mode-burst'
				burst_data = self.getAutoTargetData(burst_data, burst_or_rapid=True)
				data.append(burst_data)
			if rapid := utils.text.getProperty('Rapid', self.raw_propertiesMap):
				rapid_data = copy.deepcopy(original_data)
				rapid_data["name"] = f'{self.name} (Rapid)'

				rapid_data["system"]["actionType"] = 'save'
				rapid_data["system"]["damage"]["parts"][0][0] = re.sub(r'^(\d+)d', lambda m: f'{int(m[1])*2}d', rapid_data["system"]["damage"]["parts"][0][0])
				rapid_data["system"]["save"] = {
					"ability": 'dex',
					"dc": None,
					"scaling": 'dex'
				}
				rapid_data["flags"]["sw5e-importer"]["uid"] = f'{self.uid}.mode-rapid'
				rapid_data = self.getAutoTargetData(rapid_data, burst_or_rapid=True)
				data.append(rapid_data)

		return data

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["weaponClass"] = self.weapon_class
		data["system"]["ammo"] = { "types": self.ammo_types }

		return self.getItemVariations(data, importer)

	def getFile(self, importer):
		return self.raw_weaponClassification
