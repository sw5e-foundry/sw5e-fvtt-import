import sw5e.Entity, utils.text
import re, json

class BaseFeature(sw5e.Entity.Item):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.text = utils.text.clean(raw_item, "text")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

		self.contentSource, self.contentSourceEnum = self.getContentSource(raw_item, importer)
		self.contentType, self.contentTypeEnum = self.getContentType(raw_item, importer)
		self.requirements = self.getRequirements(raw_item, importer)

		self.type = self.getType()

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_val, self.target_unit, self.target_type = self.getTarget()
		self.range = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save = self.getAction()
		self.activation = self.getActivation()

	def getType(self):
		raise NotImplementedError

	def getContentType(self, raw_item, importer):
		contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		contentType = utils.text.clean(raw_item, "contentType")
		return contentType, contentTypeEnum

	def getContentSource(self, raw_item, importer):
		contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		contentSource = utils.text.clean(raw_item, "contentSource")
		return contentSource, contentSourceEnum

	def getRequirements(self, raw_item, importer):
		return utils.text.clean(raw_item, "requirements") or utils.text.clean(raw_item, "prerequisite")

	def getActivation(self):
		return utils.text.getActivation(self.text, self.uses, self.recharge)

	def getDuration(self):
		return utils.text.getDuration(self.text, self.name)

	def getTarget(self):
		return utils.text.getTarget(self.text, self.name)

	def getRange(self):
		return {}

	def getUses(self):
		return utils.text.getUses(self.text, self.name)

	def getAction(self):
		return utils.text.getAction(self.text, self.name)

	def getImg(self):
		raise NotImplementedError

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["img"] = self.getImg()

		data["data"]["description"] = { "value": utils.text.markdownToHtml(self.text) }
		data["data"]["requirements"] = self.requirements
		data["data"]["source"] = self.contentSource

		data["data"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation else None
		}
		data["data"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		data["data"]["target"] = {
			"value": self.target_val,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		data["data"]["range"] = self.range
		data["data"]["uses"] = {
			"value": 0,
			"max": self.uses,
			"per": self.recharge
		}
		# data["data"]["consume"] = {}
		# data["data"]["ability"] = ''

		data["data"]["actionType"] = self.action_type
		# data["data"]["attackBonus"] = 0
		# data["data"]["chatFlavor"] = ''
		# data["data"]["critical"] = None
		data["data"]["damage"] = self.damage
		data["data"]["formula"] = self.formula
		data["data"]["save"] = {
			"ability": self.save,
			"dc": None,
			"scaling": "power"
		}

		# data["data"]["recharge"] = ''

		return [data]

class Feature(BaseFeature):
	def __init__(self, raw_item, old_item, uid, importer):
		self.level = utils.text.raw(raw_item, "level")
		self.sourceEnum = utils.text.raw(raw_item, "sourceEnum")
		self.source = utils.text.clean(raw_item, "source")
		self.sourceName = utils.text.clean(raw_item, "sourceName")
		self.metadata = utils.text.raw(raw_item, "metadata")

		#TODO: Remove this once the typo is fixed
		if self.sourceName == 'Juyo/Vapaad Form': self.sourceName = 'Juyo/Vaapad Form'

		self.class_name = self.getClassName(importer)

		super().__init__(raw_item, old_item, uid, importer)


	def getType(self):
		return "classfeature" if self.source in ["Class", "Archetype"] else "feat"

	def getImg(self):
		if self.source in ['Class', 'Archetype']:
			class_abbr = {
				'Berserker': 'BSKR',
				'Consular': 'CSLR',
				'Engineer': 'ENGR',
				'Fighter': 'FGTR',
				'Guardian': 'GRDN',
				'Monk': 'MNK',
				'Operative': 'OPRT',
				'Scholar': 'SCLR',
				'Scout': 'SCT',
				'Sentinel': 'SNTL',
			}[self.class_name or self.sourceName] or 'BSKR'
			activation = {
				'bonus': 'Bonus',
				'action': 'Action',
				'reaction': 'Reaction',
				'special': 'Action',
				'none': 'Passive'
			}[self.activation] or 'Passive'
			return f'systems/sw5e/packs/Icons/Class%20Features/{class_abbr}{"-ARCH" if self.source == "Archetype" else ""}-{activation}.webp'
		else:
			name = self.sourceName
			name = re.sub(r'[ /]', r'%20', name)
			return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getClassName(self, importer):
		if self.source == 'Archetype':
			archetype = importer.get('archetype', data={ "name": self.sourceName })
			if archetype:
				return archetype.className
			else:
				self.broken_links = True

	def getRequirements(self, raw_item, importer):
		if self.level and self.level > 1: return f'{self.class_name or self.sourceName} {self.level}'
		return self.sourceName

	def getFile(self, importer):
		return f'{self.source}Feature'

	def getContentType(self, raw_item, importer):
		sourceItem = importer.get(self.source.lower(), data={ "name": self.sourceName} )
		if sourceItem:
			return sourceItem.contentType, sourceItem.contentTypeEnum
		else:
			self.broken_links = True
			return '', 0

	def getContentSource(self, raw_item, importer):
		sourceItem = importer.get(self.source.lower(), data={ "name": self.sourceName} )
		if sourceItem:
			return sourceItem.contentSource, sourceItem.contentSourceEnum
		else:
			self.broken_links = True
			return '', 0

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["className"] = self.class_name

		return [data]
