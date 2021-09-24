import sw5e.Entity, utils.text
import re, json

class Archetype(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.className = utils.text.clean(raw_item, "className")
		self.text = utils.text.clean(raw_item, "text")
		self.text2 = utils.text.raw(raw_item, "text2")
		self.leveledTableHeaders = utils.text.cleanJson(raw_item, "leveledTableHeaders")
		self.leveledTable = utils.text.cleanJson(raw_item, "leveledTable")
		self.imageUrls = utils.text.cleanJson(raw_item, "imageUrls")
		self.casterRatio = utils.text.raw(raw_item, "casterRatio")
		self.casterTypeEnum = utils.text.raw(raw_item, "casterTypeEnum")
		self.casterType = utils.text.clean(raw_item, "casterType")
		self.classCasterTypeEnum = utils.text.raw(raw_item, "classCasterTypeEnum")
		self.classCasterType = utils.text.clean(raw_item, "classCasterType")
		self.features = utils.text.raw(raw_item, "features")
		self.featureRowKeysJson = utils.text.cleanJson(raw_item, "featureRowKeys")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def process(self, old_item, importer):
		super().process(old_item, importer)

	def getFeature(self, feature_name, feature_level, importer):
		text = feature_name
		if importer:
			feature_data = { "name": feature_name, "source": "archetype", "sourceName": self.name, "level": feature_level }
			feature = importer.get('feature', data=feature_data)
			if feature and feature.foundry_id:
				text = f'@Compendium[sw5e.archetypefeatures.{feature.foundry_id}]{{{text}}}'
			else:
				self.broken_links = True
				if self.foundry_id:
					print(f'		Unable to find feature {feature_data=}')
		return text

	def getDescription(self, importer):
		md_str = f'## {self.name}\n' + self.text

		patt = r'### (?P<name>\w+(?: \w+)*)(?P<after>' # '### Fast and Agile'
		patt += r'\s*'
		patt += r'_\*\*' + self.name + r':\*\* (?P<lvl>\d+))' # '_**Acquisitions Practice:** 3rd'

		md_str = re.sub(patt, lambda x: f'### {self.getFeature(x.group("name"), x.group("lvl"), importer)}{x.group("after")}', md_str)

		return utils.text.markdownToHtml(md_str)

	def getImg(self, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = self.name if capitalized else self.name.lower()
		name = re.sub(r'[ /]', r'%20', name)
		name = re.sub(r' (.*?)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Archetypes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription(importer) }
		data["data"]["source"] = self.contentSource
		data["data"]["className"] = self.className
		data["data"]["classCasterType"] = self.classCasterType if self.classCasterType != "None" else "",

		return [data]

	def getSubItems(self, importer):
		text = self.text

		sub_items = []

		name = self.name
		if match := re.search(r' \(Companion\)', name): name = name[:match.start()]

		for match in re.finditer(r'\s### ([^\n]*)\n(?!\s*_\*\*' + name + ')', text):
			text = text[match.start():]

			expected = (self.className == 'Engineer') or (self.className == 'Scholar') or (self.className == 'Fighter') or (self.name == 'Deadeye Technique')
			if not expected:
				print(f'Possible error detected: searching for subitems of {name} which is not a scholar, engineer, or fighter archetype.')
				print(f'{self.className=}')

			pattern = r'#### (?P<name>[^\n]*\n)'
			pattern += r'(?P<text>(?:\s*_\*\*Prerequisite:\*\*(?: (?P<level>\d+)\w+(?:, \d+\w+| and \d+\w+)* level)?(?:,? (?P<prerequisite>[^_]+))?_\n)?'
			pattern += r'\s*[^#]*)\n'
			for sub_item in re.finditer(pattern, text):
				if not expected:
					print(f'	{sub_item["name"]=}')

				data = {}

				for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
					data[key] = getattr(self, key)
				data["name"] = sub_item["name"]
				data["text"] = sub_item["text"]

				data["prerequisite"] = sub_item["prerequisite"]
				data["level"] = int(sub_item["level"]) if sub_item["level"] else None
				data["source"] = 'ArchetypeInvocation'
				data["sourceName"] = self.name
				sub_items.append((data, 'feature'))

		return sub_items
