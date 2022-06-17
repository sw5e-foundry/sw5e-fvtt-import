import sw5e.Equipment, utils.text, utils.config
import re, json

class Equipment(sw5e.Equipment.Equipment):
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
		return utils.config.casting_properties if self.armor["type"] in ('focusgenerator', 'wristpad') else utils.config.armor_properties

	def getProperties(self):
		properties_list = self.getPropertiesList()
		properties = {
			**utils.text.getProperties(self.propertiesMap.values(), properties_list, error=True),
			**utils.text.getProperties(self.description, properties_list),
		}

		return properties

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
		data["data"]["properties"] = self.p_properties

		return [data]
