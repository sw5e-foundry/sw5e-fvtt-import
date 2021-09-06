import sw5e.sw5e, utils.text
import re, json

class Feature(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		self.text = utils.text.clean(raw_item, "text")
		self.level = utils.text.raw(raw_item, "level")
		self.sourceEnum = utils.text.raw(raw_item, "sourceEnum")
		self.source = utils.text.clean(raw_item, "source")
		self.sourceName = utils.text.clean(raw_item, "sourceName")
		self.metadata = utils.text.raw(raw_item, "metadata")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

		#TODO: Remove this once the typo is fixed
		if self.sourceName == 'Juyo/Vapaad Form': self.sourceName = 'Juyo/Vaapad Form'

		self.type = "classfeature" if self.source in ["Class", "Archetype"] else "feat"
		self.content_source = self.getContentSource(importer)
		self.class_name = self.getClassName(importer)
		self.uses, self.recharge = utils.text.getUses(self.text, self.name)
		self.action = utils.text.getAction(self.text, self.uses, self.recharge)

	def getClassName(self, importer):
		if self.source == 'Archetype':
			archetype = importer.get('archetype', name=self.sourceName)
			if archetype:
				return archetype.className
			else:
				self.brokenLinks = True
				return ''
		elif self.source == 'Class':
			return self.sourceName

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
			}[self.class_name] or 'BSKR'
			action = {
				'bonus': 'Bonus',
				'action': 'Action',
				'reaction': 'Reaction',
				'special': 'Action',
				'none': 'Passive'
			}[self.action] or 'Passive'
			return f'systems/sw5e/packs/Icons/Class%20Features/{class_abbr}{"-ARCH" if self.source == "Archetype" else ""}-{action}.webp'
		else:
			name = self.sourceName
			name = re.sub(r'[ /]', r'%20', name)
			return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getRequirements(self):
		if self.level and self.level > 1: return f'{self.class_name} {self.level}'
		return self.sourceName

	def getContentSource(self, importer):
		sourceItem = importer.get(self.source.lower(), name=self.sourceName)
		if sourceItem:
			return sourceItem.contentSource
		else:
			self.brokenLinks = True
			return ''

	def getData(self, importer):
		data = super().getData(importer)
		data["type"] = self.type
		data["img"] = self.getImg()

		data["data"] = {}
		data["data"]["description"] = { "value": utils.text.markdownToHtml(self.text) }
		data["data"]["requirements"] = self.getRequirements()
		data["data"]["source"] = self.content_source

		if self.action != 'none':
			data["data"]["activation"] = {
				"type": self.action,
				"cost": 1
			}

		#TODO: extract duration, target, range, uses, consume, damage and other rolls
		data["data"]["duration"] = {}
		data["data"]["target"] = {}
		data["data"]["range"] = {}
		data["data"]["uses"] = {
			"value": 0,
			"max": self.uses,
			"per": self.recharge
		}
		data["data"]["consume"] = {}
		data["data"]["ability"] = ''
		data["data"]["actionType"] = ''
		data["data"]["attackBonus"] = 0
		data["data"]["chatFlavor"] = ''
		data["data"]["critical"] = None
		data["data"]["damage"] = {
			"parts": [],
			"versatile": '',
		}
		data["data"]["formula"] = ''
		data["data"]["save"] = {}
		data["data"]["recharge"] = ''
		data["data"]["className"] = self.class_name

		return [data]

	def matches(self, *args, **kwargs):
		if not super().matches(*args, **kwargs): return False

		if len(args) >= 1:
			new_item = args[0]
			if new_item["level"] != self.level: return False
			if new_item["source"] != self.source: return False
			if new_item["sourceName"] != self.sourceName: return False

		return True
