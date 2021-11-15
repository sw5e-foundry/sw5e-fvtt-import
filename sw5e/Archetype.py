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

		self.full_name = self.name
		if self.name.endswith(' (Companion)'): self.name = self.name[:-12]

		self.sub_item_features = self.getSubItemFeatures()

	def getFeatureLink(self, feature_name, feature_level, importer):
		text = feature_name
		if importer:
			feature_data = { "name": feature_name, "source": 'archetype', "sourceName": self.full_name, "level": feature_level }
			feature = importer.get('feature', data=feature_data)
			if feature:
				if feature.foundry_id: text = f'@Compendium[sw5e.archetypefeatures.{feature.foundry_id}]{{{text}}}'
				else: self.broken_links = True
			else:
				self.broken_links = True
				if self.foundry_id: print(f'		Unable to find feature {feature_data=}')
		return text

	def getSubItemFeatures(self):
		text = self.text

		features = {}
		for match in re.finditer(r'\s### (?P<name>[^\n]*)\n(?!\s*_\*\*' + self.name + ')', text):
			text = text[match.start():]
			feature = []

			expected = (self.className == 'Engineer') or (self.className == 'Scholar') or (self.className == 'Fighter') or (self.name == 'Deadeye Technique')
			if not expected:
				print(f'Possible error detected: searching for subitems of {self.full_name} which is not a scholar, engineer, or fighter archetype.')
				print(f'{match["name"]=}')

			pattern = r'#### (?P<name>[^\n]*)\n'
			pattern += r'(?P<text>'
			pattern += r'(?:\s*_\*\*Prerequisite:\*\*'
			pattern += r'(?: (?P<level>\d+)\w+(?:, \d+\w+| and \d+\w+)* level)?'
			pattern += r'(?:,? (?P<prerequisite>[^_]+))?_\n)?'
			pattern += r'[^#]*)(?:\n|$)'

			for invocation in re.finditer(pattern, text):
				if not expected:
					print(f'	{invocation["name"]=}')

				feature.append({
					"name": invocation["name"],
					"text": invocation["text"],
					"level": int(invocation["level"]) if invocation["level"] else None,
					"prerequisite": invocation["prerequisite"],
				})

			features[match["name"]] = feature

		return features

	def getDescription(self, importer):
		text = f'## {self.full_name}\n'

		patt = r'### (?P<name>[^\n]+)' # '### Fast and Agile'
		patt += r'(?P<after>\s*'
		patt += r'_\*\*' + self.name + r':\*\* (?P<lvl>\d+)' # '_**Acquisitions Practice:** 3rd'
		patt += r'[^#]*)'

		for feature in re.finditer(patt, self.text):
			text += f'### {self.getFeatureLink(feature["name"], feature["lvl"], importer)}{feature["after"]}\n'

		for feature_name in self.sub_item_features:
			if match := re.search(f'(?<!#)### {feature_name}([^#])*', self.text):
				feature_data = { "name": feature_name, "source": 'archetype', "sourceName": self.full_name, "level": None }
				if (feature_item := importer.get('feature', data=feature_data)) and feature_item.foundry_id:
					text += f'### @Compendium[sw5e.archetypefeatures.{feature_item.foundry_id}]{{{feature_name}}}{match[1]}\n'
				else:
					self.broken_links = True
					text += f'### {feature_name}{match[1]}\n'
					for invocation in self.sub_item_features[feature_name]:
						invocation_data = { "name": invocation["name"], "source": 'archetypeInvocation', "sourceName": self.full_name, "level": invocation["level"] }
						if (invocation_item := importer.get('feature', data=invocation_data)) and invocation_item.foundry_id:
							text += f'#### @Compendium[sw5e.invocations.{invocation_item.foundry_id}]{{{invocation["name"]}}}\n{invocation["text"]}\n'
						else:
							self.broken_links = True
							text += f'#### {invocation["name"]}\n{invocation["text"]}\n'


		return utils.text.markdownToHtml(text)

	def getImg(self, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = self.full_name if capitalized else self.full_name.lower()
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Archetypes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["name"] = self.full_name
		data["data"]["description"] = { "value": self.getDescription(importer) }
		data["data"]["source"] = self.contentSource
		data["data"]["className"] = self.className
		data["data"]["classCasterType"] = self.classCasterType if self.classCasterType != "None" else "",

		return [data]

	def getSubItems(self, importer):
		sub_items = []

		for feature_name in self.sub_item_features:
			for invocation in self.sub_item_features[feature_name]:
				data = {}

				for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
					data[key] = getattr(self, key)

				data["name"] = invocation["name"]
				data["text"] = invocation["text"]
				data["level"] = invocation["level"]
				data["prerequisite"] = invocation["prerequisite"]

				data["source"] = 'ArchetypeInvocation'
				data["sourceName"] = self.full_name
				sub_items.append((data, 'feature'))

		return sub_items
