import sw5e.Equipment, utils.config, utils.object, utils.text
import re, json

class Equipment(sw5e.Equipment.Equipment):
	def process(self, importer):
		super().process(importer)

		self.uses, self.recharge = utils.text.getUses(self.raw_description, self.name)
		self.activation = utils.text.getActivation(self.raw_description, self.uses, self.recharge)
		self.armor = self.getArmor()

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

	def getEquipmentCategory(self):
		if self.raw_armorClassificationEnum == 0:
			if self.raw_equipmentCategory == 'Clothing':
				return 'clothing'
			if self.name.lower().find('focus generator') != -1:
				return 'focusgenerator'
			if self.name.lower().find('wristpad') != -1:
				return 'wristpad'
			return 'trinket'
		return self.raw_armorClassification.lower()

	def getArmor(self):
		ac = None
		max_dex = None

		ac = re.search(r'^\+?(\d+)', f'{self.raw_ac}')
		if ac != None: ac = int(ac.group(1))

		if self.isArmor():
			if self.category == 'medium': max_dex = 2
			elif self.category == 'heavy': max_dex = 0

		return {
			"value": ac,
			"dex": max_dex
		}

	def getPropertiesList(self):
		if self.isArmor() or self.category == 'clothing': return utils.config.armor_properties
		if self.isCastingFocus(): return utils.config.casting_properties
		return None

	def getProperties(self):
		properties = {}
		properties_list = self.getPropertiesList()
		if properties_list:
			properties = {
				**utils.text.getProperties(self.raw_propertiesMap.values(), properties_list, error=True),
				**utils.text.getProperties(self.raw_description, properties_list),
			}
			properties = utils.object.applyType(properties, properties_list)
		if self.raw_stealthDisadvantage: properties["stealthDisadvantage"] = True

		return properties

	def getBaseItem(self):
		mapping = {
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
		return mapping.get(self.name, super().getBaseItem())

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["armor"] = self.armor
		data["system"]["strength"] = self.raw_strengthRequirement or 0

		return [data]

	def isArmor(self):
		return self.category in ('light', 'medium', 'heavy', 'shield')

	def isCastingFocus(self):
		return self.category in ('focusgenerator', 'wristpad')

