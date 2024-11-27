import sw5e.Equipment, sw5e.templates, sw5e.Damage, utils.config, utils.object, utils.text
import re, json, copy

class Weapon(
	sw5e.Equipment.Equipment,
	# sw5e.templates.Mountable, # NotImplemented
):
	def load(self, raw_item):
		self.wpn_damage = self.getDamage()
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
		rang = None
		for prop in ('Power Cell', 'Slug Cartridge', 'Thrown', 'Range', 'Special'): rang = rang or utils.text.getProperty(prop, self.raw_propertiesMap)
		if not rang or rang == 'special': pass
		elif type(rang) == list: short_range, long_range = rang
		else: short_range = int(rang)

		return short_range, long_range, 'ft'

	def getAction(self):
		return self.getActionType(), sw5e.Damage.DamageGroup([]), None, None, None, None

	def getImg(self, importer=None):
		kwargs = {
			'item_type': self.raw_weaponClassification,
			# 'no_img': ('Unknown',),
			'default_img': 'modules/sw5e/icons/packs/Simple%20Blasters/Hold-out.webp',
			'plural': True
		}
		return super().getImg(importer=importer, **kwargs)

	def getActionType(self):
		if self.category in ('simpleBL', 'martialBL'):
			return 'rwak'
		else:
			return 'mwak'

	def getDamage(self):
		base, versatile = sw5e.Damage.Damage(validate=False), sw5e.Damage.Damage(validate=False)

		base.number = self.raw_damageNumberOfDice or 1
		if self.raw_damageDieType == -1:
			_, damage, other_formula, _, _, _ = utils.text.getAction(self.raw_description, self.raw_name)
			base = sw5e.Damage.Damage.fromOldFormat(other_formula) or damage.parts[0]
			if len(damage.parts) == 2: versatile = damage.parts[1]
		elif self.raw_damageDieType >= 1:
			base.denomination = self.raw_damageDieType

		if (dType := self.raw_damageType.lower()) != 'unknown': base.types = ['thunder' if dType == 'sonic' else dType]

		versatile_prop = utils.text.getProperty('Versatile', self.raw_propertiesMap) or ''
		if match := re.search(r'(?P<number>\d*)d(?P<denom>\d+)', versatile_prop):
			versatile.number = match["number"] or base.number
			versatile.denomination = match["denom"] or base.number
			versatile.types = base.types

		return {
			"base": base,
			"versatile": versatile,
		}

	def getWeaponClass(self):
		if self.category == 'natural' or self.raw_fakeItem: return ''
		for (classification, wpns) in utils.config.weapon_classes.items():
			if self.name.lower() in wpns:
				return classification
		else: raise ValueError(self.name)

	def getAmmoTypes(self):
		if (self.name == "Blaster Cannon"): return ['powerGenerator']
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
			# **utils.text.getProperties(self.raw_description, properties_list),
		}

		return utils.object.applyType(properties, properties_list)

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
			data = [original_data]

		return data

	def getData(self, importer):
		data = super().getData(importer)[0]

		# ammunition
		# damage
		if (base := self.wpn_damage["base"]).valid(): utils.object.setProperty(data, 'system.damage.base', base.getData(), force=True)
		if (vers := self.wpn_damage["versatile"]).valid(): utils.object.setProperty(data, 'system.damage.versatile', vers.getData(), force=True)
		# magicalBonus
		# mastery
		# properties
		## done in Equipment.py
		# proficient
		# range
		utils.object.setProperty(data, 'system.range.value', self.range_short, force=True)
		utils.object.setProperty(data, 'system.range.long', self.range_long or None, force=True)
		utils.object.setProperty(data, 'system.range.units', self.range_unit or 'ft', force=True)

		# sw5e specific stuff
		utils.object.setProperty(data, 'system.weaponClass', self.weapon_class, force=True)
		utils.object.setProperty(data, 'flags.sw5e.reload.types', self.ammo_types, force=True)

		return self.getItemVariations(data, importer)

	def getFile(self, importer):
		return self.raw_weaponClassification

	############################
	#    Template Functions    #
	############################

	# templates.Activities
	def processActivitiesData(self, importer):
		data = super().processActivitiesData(importer)
		if "reach" in self.p_properties: data["range"]["reach"] = 10
		return data

	# templates.ItemDescription
	def getDescription(self):
		properties = {prop: self.raw_propertiesMap[prop] for prop in self.raw_propertiesMap if prop != 'Special'}

		text = ''

		text = ', '.join([properties[prop].capitalize() for prop in properties if prop != 'Ammunition'])
		text = utils.text.markdownToHtml(text) or ''

		if 'Special' in self.raw_propertiesMap:
			if text: text += '\n'
			if (special := self.raw_propertiesMap["Special"]).lower() != "special":
				text += utils.text.markdownToHtml('#### Special\n' + special)
			elif self.raw_description:
				text += utils.text.markdownToHtml('#### Special\n' + self.raw_description)
			else:
				raise ValueError
		elif self.raw_description:
			text += utils.text.markdownToHtml('#### Description\n' + self.raw_description)

		return text
	def processDescription(self, importer):
		if importer:
			properties = {prop: self.raw_propertiesMap[prop] for prop in self.raw_propertiesMap if prop != 'Special'}

			text = ''

			def getContent(prop_name):
				prop = importer.get('WeaponProperty', data={'name': prop_name})
				if prop: return prop.getContent(val=properties[prop_name])
				else: return properties[prop_name].capitalize()
			text = '\n'.join([getContent(prop) for prop in properties])

			if 'Special' in self.raw_propertiesMap:
				if text: text += '\n'
				if (special := self.raw_propertiesMap["Special"]).lower() != "special":
					text += utils.text.markdownToHtml('#### Special\n' + special)
				elif self.raw_description:
					text += utils.text.markdownToHtml('#### Special\n' + self.raw_description)
				else:
					raise ValueError
			elif self.raw_description:
				text += utils.text.markdownToHtml('#### Description\n' + self.raw_description)

			self.description = text

	# templates.Identifiable

	# template.ItemType
	def getCategory(self):
		wc = self.raw_weaponClassification

		start = ''
		for training in ('Simple', 'Martial', 'Exotic'):
			if wc.startswith(training): start = training.lower()

		if wc.endswith('Blaster') or self.getProperty('Ammunition') or self.getProperty('Reload'):
			return f'{start}BL'
		for mode in ('Vibroweapon', 'Lightweapon'):
			if wc.endswith(mode): return f'{start}{mode[0]}W'

		if wc == 'Natural': return 'natural'

		return 'improv'

	# template.PhysicalItem

	# templates.EquippableItem

#