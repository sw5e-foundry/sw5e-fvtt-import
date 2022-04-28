import sw5e.Equipment, utils.text
import re, json

class Equipment(sw5e.Equipment.Equipment):
	armor_properties = {
		"Absorptive": 'Absorptive',
		"Agile": 'Agile',
		"Anchor": 'Anchor',
		"Avoidant": 'Avoidant',
		"Barbed": 'Barbed',
		"Bulky": 'Bulky',
		"Charging": 'Charging',
		"Concealing": 'Concealing',
		"Cumbersome": 'Cumbersome',
		"Gauntleted": 'Gauntleted',
		"Imbalanced": 'Imbalanced',
		"Impermeable": 'Impermeable',
		"Insulated": 'Insulated',
		"Interlocking": 'Interlocking',
		"Lambent": 'Lambent',
		"Lightweight": 'Lightweight',
		"Magnetic": 'Magnetic',
		"Obscured": 'Obscured',
		"Obtrusive": 'Obtrusive',
		"Powered": 'Powered',
		"Reactive": 'Reactive',
		"Regulated": 'Regulated',
		"Reinforced": 'Reinforced',
		"Responsive": 'Responsive',
		"Rigid": 'Rigid',
		"Silent": 'Silent',
		"Spiked": 'Spiked',
		"Strength": 'Strength',
		"Steadfast": 'Steadfast',
		"Versatile": 'Versatile',
	}
	casting_properties = {
		"c_Absorbing": 'Absorbing',
		"c_Acessing": 'Acessing',
		"c_Amplifying": 'Amplifying',
		"c_Bolstering": 'Bolstering',
		"c_Constitution": 'Constitution',
		"c_Dispelling": 'Dispelling',
		"c_Elongating": 'Elongating',
		"c_Enlarging": 'Enlarging',
		"c_Expanding": 'Expanding',
		"c_Extending": 'Extending',
		"c_Fading": 'Fading',
		"c_Focused": 'Focused',
		"c_Increasing": 'Increasing',
		"c_Inflating": 'Inflating',
		"c_Mitigating": 'Mitigating',
		"c_Ranging": 'Ranging',
		"c_Rending": 'Rending',
		"c_Repelling": 'Repelling',
		"c_Storing": 'Storing',
		"c_Surging": 'Surging',
		"c_Withering": 'Withering',
	}

	def load(self, raw_item):
		super().load(raw_item)

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.uses, self.recharge = utils.text.getUses(self.description, self.name)
		self.activation = utils.text.getActivation(self.description, self.uses, self.recharge)
		self.armor = self.getArmor()
		self.p_properties = self.getProperties()

	def getImg(self, importer=None):
		kwargs = {
			'item_type': self.equipmentCategory,
			'no_img': ('Unknown', 'Clothing'),
			'default_img': 'systems/sw5e/packs/Icons/Armor/PHB/AssaultArmor.webp',
			# 'plural': False
		}
		if self.equipmentCategory == 'Armor': kwargs["item_type"] += '/' + self.contentSource
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		properties = {prop: self.propertiesMap[prop] for prop in self.propertiesMap if prop != 'Special'}

		text = ''

		if importer:
			def getContent(prop_name):
				prop = importer.get('armorProperty', data={'name': prop_name})
				if prop: return prop.getContent(val=properties[prop_name])
				else: return properties[prop_name].capitalize()
			text = '\n'.join([getContent(prop) for prop in properties])
		else:
			text = ', '.join([properties[prop].capitalize() for prop in properties])
			text = utils.text.markdownToHtml(text)

		if self.description:
			if text: text += '\n<hr/>\n'
			text += utils.text.markdownToHtml(self.description)

		return text

	def getArmor(self):
		ac = None
		equipment_type = None
		max_dex = None

		if self.armorClassificationEnum == 0:
			if self.equipmentCategory == 'Clothing':
				equipment_type = 'clothing'
			elif self.name.lower().find('focus generator') != -1:
				equipment_type = 'focusgenerator'
			elif self.name.lower().find('wristpad') != -1:
				equipment_type = 'wristpad'
			else:
				equipment_type = 'trinket'
		else:
			ac = re.search(r'^\+?(\d+)', self.ac)
			if ac != None: ac = int(ac.group(1))
			equipment_type = self.armorClassification.lower()

		if self.armorClassification == 'Medium': max_dex = 2
		if self.armorClassification == 'Heavy': max_dex = 0

		return {
			"value": ac,
			"type": equipment_type,
			"dex": max_dex
		}

	def getPropertiesList(self):
		return self.casting_properties if self.armor["type"] in ('focusgenerator', 'wristpad') else self.armor_properties

	def getProperties(self):
		properties_list = self.getPropertiesList()
		properties = {
			**utils.text.getProperties(self.propertiesMap.values(), properties_list.values(), error=True),
			**utils.text.getProperties(self.description, properties_list.values()),
		}

		return {
			key: properties[properties_list[key].lower()]
			for key in properties_list.keys()
			if (properties_list[key].lower() in properties)
		}

	def getBaseItem(self):
		override = {
			"Bone light shield": 'lightphysicalshield',
			"Crystadium medium shield": 'mediumphysicalshield',
			"Quadanium heavy shield": 'heavyphysicalshield',

			"Durafiber combat suit": 'combatsuit',
			"Duravlex fiber armor": 'fiberarmor',
			"Fleximetal fiber armor": 'fiberarmor',

			"Beskar weave armor": 'weavearmor',
			"Neutronium mesh": 'mesharmor',
			"Plastoid composite": 'compositearmor',

			"Duranium battle armor": 'battlearmor',
			"Durasteel exoskeleton": 'heavyexoskeleton',
			"Laminanium assault": 'assaultarmor',

			"Storing, withering focus generator": 'focusgenerator',
			"Repelling wristpad": 'wristpad',
		}
		return override.get(self.name, super().getBaseItem())

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["armor"] = self.armor
		data["data"]["strength"] = self.strengthRequirement
		data["data"]["stealth"] = self.stealthDisadvantage
		if self.armor["type"] in ('focusgenerator', 'wristpad'):
			data["data"]["properties"] = { f'c_{prop}': self.p_properties.get(prop.lower(), None) for prop in self.casting_properties }
		else:
			data["data"]["properties"] = { prop: self.p_properties.get(prop.lower(), None) for prop in self.armor_properties }

		return [data]
