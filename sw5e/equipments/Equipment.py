import sw5e.Equipment, utils.config, utils.object, utils.text
import re, json

class Equipment(sw5e.Equipment.Equipment):
	def process(self, importer):
		super().process(importer)

		self.uses, self.recharge = utils.text.getUses(self.raw_description, self.name)
		self.activation = utils.text.getActivation(self.raw_description, self.uses, self.recharge)
		self.armor = self.getArmor()
		self.p_properties = self.getProperties()

	def getImg(self, importer=None):
		kwargs = {
			'item_type': self.raw_equipmentCategory,
			'no_img': ('Unknown'),
			'default_img': 'systems/sw5e/packs/Icons/Armor/PHB/AssaultArmor.webp',
			# 'plural': False
		}
		if self.raw_equipmentCategory == 'Armor': kwargs["item_type"] += '/' + self.raw_contentSource
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		properties = {prop: self.raw_propertiesMap[prop] for prop in self.raw_propertiesMap if prop != 'Special'}

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

		if self.raw_description:
			if text: text += '\n<hr/>\n'
			text += utils.text.markdownToHtml(self.raw_description)

		return text

	def getArmor(self):
		ac = None
		equipment_type = None
		max_dex = None

		if self.raw_armorClassificationEnum == 0:
			if self.raw_equipmentCategory == 'Clothing':
				equipment_type = 'clothing'
			elif self.name.lower().find('focus generator') != -1:
				equipment_type = 'focusgenerator'
			elif self.name.lower().find('wristpad') != -1:
				equipment_type = 'wristpad'
			else:
				equipment_type = 'trinket'
		else:
			ac = re.search(r'^\+?(\d+)', f'{self.raw_ac}')
			if ac != None: ac = int(ac.group(1))
			equipment_type = self.raw_armorClassification.lower()

		if self.raw_armorClassification == 'Medium': max_dex = 2
		if self.raw_armorClassification == 'Heavy': max_dex = 0

		return {
			"value": ac,
			"type": equipment_type,
			"dex": max_dex
		}

	def getPropertiesList(self):
		return utils.config.casting_properties if self.armor["type"] in ('focusgenerator', 'wristpad') else utils.config.armor_properties

	def getProperties(self):
		properties_list = self.getPropertiesList()
		properties = {
			**utils.text.getProperties(self.raw_propertiesMap.values(), properties_list, error=True),
			**utils.text.getProperties(self.raw_description, properties_list),
		}

		return utils.object.applyType(properties, properties_list)

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

		data["system"]["armor"] = self.armor
		data["system"]["strength"] = self.raw_strengthRequirement or 0
		data["system"]["stealth"] = self.raw_stealthDisadvantage
		data["system"]["properties"] = self.p_properties

		return [data]
