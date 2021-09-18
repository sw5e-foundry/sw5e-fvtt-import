import sw5e.Equipment, utils.text
import re, json

class Equipment(sw5e.Equipment.Equipment):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.type = 'equipment'

		self.uses, self.recharge = utils.text.getUses(self.description, self.name)
		self.action = utils.text.getActivation(self.description, self.uses, self.recharge)

	def getImg(self):
		kwargs = {
			'item_type': self.equipmentCategory,
			'no_img': ('Unknown', 'Clothing'),
			'default_img': 'systems/sw5e/packs/Icons/Armor/PHB/Assault%20Armor.webp',
			# 'plural': False
		}
		if self.equipmentCategory == 'Armor': kwargs["item_type"] += '/' + self.contentSource
		return super().getImg(**kwargs)

	def getDescription(self, importer):
		properties = self.propertiesMap
		properties = {prop: properties[prop] for prop in self.propertiesMap if prop != 'Special'}

		text = ''

		if importer:
			def getContent(prop_name):
				prop = importer.get('armorProperty', data={'name': prop_name})
				if prop: return prop.getContent(val=properties[prop_name])
				else: return properties[prop_name].capitalize()
			text = '\n'.join([getContent(prop) for prop in properties])
		else:
			text = ', '.join([properties[prop].capitalize() for prop in properties])

		if self.description:
			if text: text += '\n<hr/>\n'
			text += self.description

		return utils.text.markdownToHtml(text)

	def getArmor(self):
		ac = None
		equipment_type = None
		max_dex = None

		if self.armorClassificationEnum == 0:
			if self.equipmentCategory == 'Clothing':
				equipment_type = 'clothing'
			else:
				equipment_type = 'trinket'
		else:
			ac = re.search(r'^(\d+)', self.ac)
			if ac != None: ac = int(ac.group(1))
			equipment_type = self.armorClassification.lower()

		if self.armorClassification == 'Medium': max_dex = 2
		if self.armorClassification == 'Heavy': max_dex = 0

		return {
			"value": ac,
			"type": equipment_type,
			"dex": max_dex
		}

	def getProperties(self):
		armor_properties = [
			'Absorptive',
			'Agile',
			'Anchor',
			'Avoidant',
			'Barbed',
			'Bulky',
			'Charging',
			'Concealing',
			'Cumbersome',
			'Gauntleted',
			'Imbalanced',
			'Impermeable',
			'Insulated',
			'Interlocking',
			'Lambent',
			'Lightweight',
			'Magnetic',
			'Obscured',
			'Obtrusive',
			'Powered',
			'Reactive',
			'Regulated',
			'Reinforced',
			'Responsive',
			'Rigid',
			'Silent',
			'Spiked',
			'Strength',
			'Steadfast',
			'Versatile'
		]
		return { prop: prop in self.propertiesMap for prop in armor_properties }

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["armor"] = self.getArmor()
		data["data"]["strength"] = self.strengthRequirement
		data["data"]["stealth"] = self.stealthDisadvantage
		data["data"]["properties"] = self.getProperties()

		return [data]
