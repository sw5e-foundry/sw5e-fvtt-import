import sw5e.sw5e
import re

class Feature(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		def raw(attr): return attr and raw_item[attr]
		def clean(attr): return attr and self.cleanStr(raw_item[attr])
		def cleanJson(attr): return attr and (clean(attr+"Json") or '  ')[2:-2].split('","')

		self.text = clean("text")
		self.level = raw("level")
		self.sourceEnum = raw("sourceEnum")
		self.source = clean("source")
		self.sourceName = clean("sourceName")
		self.metadata = raw("metadata")
		self.partitionKey = clean("partitionKey")
		self.rowKey = clean("rowKey")

		#TODO: Remove this once the typo is fixed
		if self.sourceName == 'Juyo/Vapaad Form': self.sourceName = 'Juyo/Vaapad Form'

		self.type = "classfeature" if self.source in ["Class", "Archetype"] else "feat"
		self.content_source = self.getContentSource(importer)
		self.class_name = self.getClassName(importer)
		self.action = self.getAction()

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

	def getAction(self):
		src = self.text
		if re.search(r'bonus action', src):
			return 'bonus'
		elif re.search(r'as an action|can take an action', src):
			return 'action'
		elif re.search(r'you can use your reaction|using your reaction|you can use this special reaction', src):
			return 'reaction'
		else:
			return 'none'

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
				'none': 'Passive'
			}[self.action] or 'Passive'
			return f'systems/sw5e/packs/Icons/Class%20Features/{class_abbr}{"-ARCH" if self.source == "Archetype" else ""}-{action}.webp'
		else:
			name = self.sourceName
			name = re.sub(r",", r"", name)
			# name = re.sub(r"'", r"_", name)
			name = re.sub(r"Twi'lek", r"Twi_lek", name)
			name = re.sub(r"Hutt, Adolescent", r"Hutt", name)
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
		data["data"]["description"] = { "value": self.markdownToHtml(self.text) }
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
		data["data"]["uses"] = {}
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

		return data

	def matches(self, *args, **kwargs):
		if not super().matches(*args, **kwargs): return False

		if len(args) >= 1:
			new_item = args[0]
			if new_item["level"] != self.level: return False
			if new_item["source"] != self.source: return False
			if new_item["sourceName"] != self.sourceName: return False

		return True
