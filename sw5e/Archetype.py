import sw5e.Entity, utils.text
import re, json

class Archetype(sw5e.Entity.Item):
	def load(self, raw_archetype):
		super().load(raw_archetype)

		attrs = [
			"className",
			"text",
			"text2",
			"leveledTableHeaders",
			"leveledTable",
			"imageUrls",
			"casterRatio",
			"casterTypeEnum",
			"casterType",
			"classCasterTypeEnum",
			"classCasterType",
			"features",
			"featureRowKeysJson",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"timestamp",
			"rowKey",
		]
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_archetype, attr))

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.full_name = self.name
		if self.name.endswith(' (Companion)'): self.name = self.name[:-12]

		self.features, self.invocations = self.getFeatures(importer)
		self.advancements = self.getAdvancements()

	def getFeatures(self, importer):
		text = self.raw_text

		features = {}
		invocations = {}

		levels_pat = r'(?P<level>\d+)\w+(?:, \d+\w+|,? and \d+\w+)* level'
		feature_pat = r'(?<!#)###(?!#) (?P<name>[^\n]*)\s*';
		feature_prereq_pat = fr'_\*\*{self.name}:\*\* {levels_pat}_\s*';
		invocat_pat = r'(?<!#)####(?!#) (?P<name>[^\n]*)\s*';
		invocat_prereq_pat = fr'_\*\*Prerequisite:\*\* (?:{levels_pat})?(?:, )?(?P<prerequisite>[^\n]*)_\s*';
		for match in re.finditer(feature_pat, text):
			feature_name = match["name"]
			subtext = text[match.end():]
			if (next_feature := re.search(feature_pat, subtext)): subtext = subtext[:next_feature.start()]

			# If there is a prerequisite, it's a normal feature
			match = re.match(feature_prereq_pat, subtext)
			if match:
				level = match["level"]
				subtext = subtext[match.end():]

				feature_data = { "name": feature_name, "source": 'Archetype', "sourceName": self.full_name, "level": level }
				feature = importer.get('feature', data=feature_data)
				if feature:
					if level not in features: features[level] = {}
					features[level][feature_name] = {
						"name": feature_name,
						"level": level,
						"foundry_id": feature.foundry_id,
						"uid": feature.uid,
						"description": subtext.strip()
					}
					if not feature.foundry_id: self.broken_links = True
				else:
					if self.foundry_id: print(f'		Unable to find feature {feature_data=}')
					self.broken_links = True

			# Otherwise, it's a list of invocations
			if (not match) or (feature_name == "Additional Maneuvers"):
				expected = (self.raw_className in ['Engineer', 'Scholar', 'Fighter']) or (self.name == 'Deadeye Technique')
				if not expected:
					print(f'Possible error detected: searching for subitems of {self.full_name} which is not a scholar, engineer, or fighter archetype.')
					print(f'{match["name"]=}')
				invocation_list = []
				for match in re.finditer(fr'{invocat_pat}(?P<text>(?:{invocat_prereq_pat})?[^#]*)', subtext):
					if not expected: print(f'	{match["name"]=}')
					invocation_list.append(match.groupdict())
				invocations[feature_name] = invocation_list

		for name, invocation in invocations.items():
			if not len(invocation):
				raise ValueError(f'Invocation type "{name}" detected with no invocations.')

		return features, invocations

	def getAdvancements(self):
		advancements = [ ]
		for level in self.features:
			uids = []
			for name in self.features[level]:
				feature = self.features[level][name]
				uids.append(f'Compendium.sw5e.archetypefeatures.{feature["foundry_id"]}')
			if len(uids):
				advancements.append( sw5e.Advancement.ItemGrant(name="Features", uids=uids, level=level) )
		return advancements

	def getDescription(self, importer):
		text = self.raw_text
		if match := re.search(r'#{3}', text):
			text = text[:match.start()]

		text = f'## {self.full_name}\n' + text

		return utils.text.markdownToHtml(text)

	def getImg(self, importer=None, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = utils.text.slugify(self.full_name, capitalized=capitalized)
		return f'systems/sw5e/packs/Icons/Archetypes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["-=className"] = None

		data["name"] = self.full_name
		data["data"]["description"] = { "value": self.getDescription(importer) }
		data["data"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["data"]["classIdentifier"] = utils.text.slugify(self.raw_className, capitalized=False)
		data["data"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["data"]["source"] = self.raw_contentSource
		data["data"]["classCasterType"] = self.raw_classCasterType if self.raw_classCasterType != "None" else ""

		return [data]

	def getSubEntities(self, importer):
		sub_items = []

		for feature_name in self.invocations:
			for invocation in self.invocations[feature_name]:
				data = {}

				for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
					data[key] = getattr(self, f'raw_{key}')

				data["name"] = invocation["name"]
				data["text"] = invocation["text"]
				data["level"] = int(invocation["level"]) if invocation["level"] else None
				data["prerequisite"] = invocation["prerequisite"]

				data["source"] = 'ArchetypeInvocation'
				data["sourceName"] = self.full_name
				sub_items.append((data, 'feature'))

		return sub_items
