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

		self.sourceClass = self.getSourceClass(importer)
		self.features, self.invocations = self.getFeatures(importer)
		self.force, self.tech, self.superiority = self.getProgression(importer)
		self.advancements = self.getAdvancements()

	def getSourceClass(self, importer):
		if importer:
			class_data = { "name": self.raw_className }
			return importer.get('class', data=class_data)
		self.broken_links = True

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

	def getProgression(self, importer):
		force, tech, superiority = 'none', 'none', 'none'

		features = [self.features[level][name] for level in self.features for name in self.features[level]]

		if len(filtered := [ feature for feature in features if re.match(fr"(?:Improved )?Forcecasting$", feature["name"]) ]):
			source = self.sourceClass.force if self.sourceClass else 'none'
			if source == 'none': force = 'arch'
			elif source == 'arch': force = 'half'
			elif source == 'half': force = '3/4'
			elif source == '3/4': force = 'full'
			else: raise ValueError(source, filtered)

		if len(filtered := [ feature for feature in features if re.match(fr"(?:Improved )?Techcasting$", feature["name"]) ]):
			source = self.sourceClass.tech if self.sourceClass else 'none'
			if source == 'none': tech = 'arch'
			elif source == 'arch': tech = 'half'
			elif source == 'half': tech = '3/4'
			elif source == '3/4': tech = 'full'
			else: raise ValueError(source, filtered)

		if len(filtered := [ feature for feature in features if re.match(fr"(?:Improved )?Superiority$", feature["name"]) ]):
			source = self.sourceClass.superiority if self.sourceClass else '0.0'
			if source == '0.0': superiority = '0.5'
			elif source == '0.5': superiority = '1'
			else: raise ValueError(source, filtered)

		return force, tech, superiority

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

	def getDescription(self):
		text = self.raw_text
		if match := re.search(r'#{3}', text):
			text = text[:match.start()]

		text = f'## {self.full_name}\n' + text

		return utils.text.markdownToHtml(text)

	def getInvocationsText(self, importer):
		output = []
		if importer:
			for feature_name in self.invocations:
				output += [f'<h1>{feature_name}</h1>']
				output += ['<ul>']
				for invocation in self.invocations[feature_name]:
					invocation_data = {}
					for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
						invocation_data[key] = getattr(self, f'raw_{key}')

					invocation_data["name"] = invocation["name"]
					invocation_data["text"] = invocation["text"]
					invocation_data["level"] = int(invocation["level"]) if invocation["level"] else None
					invocation_data["prerequisite"] = invocation["prerequisite"]

					invocation_data["source"] = 'ArchetypeInvocation'
					invocation_data["sourceName"] = self.name

					invocation = importer.get('feature', data=invocation_data)
					if invocation:
						output += [f'<li>@Compendium[sw5e.invocations.{invocation.foundry_id}]{{{invocation.name.capitalize()}}}</li>']
						if not invocation.foundry_id: self.broken_links = True
					else:
						if self.foundry_id: print(f'		Unable to find invocation {invocation_data=}')
						self.broken_links = True
				output += ['</ul>']

		return "\n".join(output)

	def getImg(self, importer=None, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = utils.text.slugify(self.full_name, capitalized=capitalized)
		return f'systems/sw5e/packs/Icons/Archetypes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["name"] = self.full_name
		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["invocations"] = { "value": self.getInvocationsText(importer) }
		data["data"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["data"]["classIdentifier"] = utils.text.slugify(self.raw_className, capitalized=False)
		data["data"]["powercasting"] = { "force": self.force, "tech": self.tech }
		data["data"]["superiority"] = { "progression": self.superiority }
		data["data"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["data"]["source"] = self.raw_contentSource

		data["data"]["-=className"] = None
		data["data"]["-=classCasterType"] = None
		data["data"]["powercasting"]["-=progression"] = None
		data["data"]["powercasting"]["-=ability"] = None

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
