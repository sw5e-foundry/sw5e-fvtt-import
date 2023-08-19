import sw5e.Entity, utils.text
import re, json

class Archetype(sw5e.Entity.Item):
	def getAttrs(self):
		return super().getAttrs() + [
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

	def load(self, raw_archetype):
		super().load(raw_archetype)

		self.full_name = self.name
		if self.name.endswith(' (Companion)'): self.name = self.name[:-12]
		self.sourceClass = None
		self.description = self.loadDescription()
		self.features, self.invocations = self.loadFeatures()
		self.force, self.tech, self.superiority = self.loadProgression()
		self.formulas = self.loadFormulas()
		self.advancements = self.loadAdvancements()
		self.invocationsText = ""

	def loadDescription(self):
		text = self.raw_text
		if match := re.search(r'#{3}', text):
			text = text[:match.start()]

		text = f'## {self.full_name}\n' + text

		return utils.text.markdownToHtml(text)

	def loadFeatures(self):
		text = self.raw_text

		features = {}
		invocations = {}

		not_a_feature = '|'.join(("GM Consideration",))
		arch_name = '|'.join((re.sub(r'([()])', r'\\\1', name) for name in (self.name, self.full_name)))

		it = utils.text.exactly_x_times(r'[_*]', 1)
		b = utils.text.exactly_x_times(r'[_*]', 2)
		ib = utils.text.exactly_x_times(r'[_*]', 3)
		h3 = utils.text.exactly_x_times(r'#', 3)
		h4 = utils.text.exactly_x_times(r'#', 4)

		levels_pat = fr'(?P<level>\d+)\w+(?:, \d+\w+|,? and \d+\w+)* level'
		feature_pat = fr'{h3} (?!{not_a_feature})(?P<name>[^\n]*)\s*';
		feature_prereq_pat = fr'{ib}(?:{arch_name}):{b} {levels_pat}{it}\s*';
		invocat_pat = fr'{h4} (?!{not_a_feature})(?P<name>[^\n]*)\s*';
		invocat_prereq_pat = fr'{ib}Prerequisite:{b} (?:{levels_pat})?(?:, )?(?P<prerequisite>[^\n]*){it}\s*';

		for match in re.finditer(feature_pat, text):
			feature_name = match["name"]

			subtext = text[match.end():]
			if (next_feature := re.search(feature_pat, subtext)):
				subtext = subtext[:next_feature.start()]


			# If there is a prerequisite, it's a normal feature
			if (feature_name != "Additional Maneuvers") and (match := re.match(feature_prereq_pat, subtext)):
				level = match["level"]
				subtext = subtext[match.end():]
				feature_data = {
					"name": feature_name,
					"source": 'Archetype',
					"sourceName": self.full_name,
					"level": level,
				}

				if level not in features: features[level] = {}
				features[level][feature_name] = {
					"name": feature_name,
					"level": level,
					"description": subtext.strip(),
					"uid": self.getUID(feature_data, 'Feature'),
				}

			# Otherwise, it's a list of invocations
			else:
				expected = (self.raw_className in ['Engineer', 'Scholar', 'Fighter']) or (self.name == 'Deadeye Technique')
				if not expected:
					print(f'Possible error detected: searching for subitems of {self.full_name} which is not a scholar, engineer, or fighter archetype.')
					if match: print(f'{match["name"]=}')
				invocation_category = feature_name
				if invocation_category not in invocations: invocations[invocation_category] = {}
				for match in re.finditer(fr'{invocat_pat}(?P<text>(?:{invocat_prereq_pat})?[^#]*)', subtext):
					invocation_name = match["name"]
					level = match["level"]
					invocation_text = match["text"]
					if not expected: print(f'	{invocation_name=}')

					invocation_data = {
						"name": invocation_name,
						"text": invocation_text,
						"level": int(level) if level else None,
						"prerequisite": match["prerequisite"],
						"source": 'ClassInvocation',
						"sourceName": self.name
					}

					invocations[invocation_category][invocation_name] = {
						"name": invocation_name,
						"level": level,
						"text": invocation_text,
						"prerequisite": match["prerequisite"],
						"uid": self.getUID(invocation_data, 'Feature'),
					}

		for name, invocation in invocations.items():
			if not len(invocation):
				print(json.dumps(invocations, indent=4, sort_keys=False, ensure_ascii=False))
				raise ValueError(f'Invocation type "{name}" detected with no invocations.', self.full_name)

		return features, invocations

	def loadProgression(self):
		force, tech, superiority = 'none', 'none', '0'

		features = [feature for features in self.features.values() for feature in features.values()]

		if len(filtered := [ feature for feature in features if re.match(fr"(?:Improved )?Forcecasting$", feature["name"]) ]):
			force = 'arch'

		if len(filtered := [ feature for feature in features if re.match(fr"(?:Improved )?Techcasting$", feature["name"]) ]):
			tech = 'arch'

		if len(filtered := [ feature for feature in features if re.match(fr"(?:Improved )?Superiority$", feature["name"]) ]):
			superiority = '0.5'

		return force, tech, superiority

	def loadFormulas(self):
		formulas = {}

		# nope = [
		# 	'level',
		# 	'proficiency bonus',
		# 	'features',
		# 	'force points',
		# 	'force powers known',
		# 	'tech points',
		# 	'tech powers known',
		# 	'max power level',
		# ]

		# for name in self.raw_levelChangeHeaders:
		# 	if name in nope: continue
		# 	formulas[name] = { "name": name, "values": {} }

		# for lvl, data in self.raw_levelChanges.items():
		# 	for name, value in data.items():
		# 		if name in formulas:
		# 			formulas[name]["values"][lvl] = value

		return formulas

	def loadAdvancements(self):
		advancements = []

		for formula in self.formulas.values():
			advancements.append( sw5e.Advancement.ScaleValue(name=formula.name, values=formula.values) )

		return advancements



	def process(self, importer):
		super().process(importer)

		if importer:
			self.processSourceClass(importer)
			self.processFeatures(importer)
			self.processInvocationsText(importer)
			self.processProgression()
			self.processAdvancements()
		else:
			self.broken_links += ['no importer']

	def processSourceClass(self, importer):
		class_data = { "name": self.raw_className }
		self.sourceClass = importer.get('class', data=class_data)

	def processFeatures(self, importer):
		for level, features in self.features.items():
			for feature in features.values():
				if entity := importer.get('feature', uid=feature["uid"]):
					feature["foundry_id"] = entity.foundry_id
				else:
					print(f'		Unable to find feature {feature=}')
					self.broken_links += [f'cant find feature {feature["name"]}']

		for invocation_type, invocations in self.invocations.items():
			for invocation in invocations.values():
				if entity := importer.get('feature', uid=feature["uid"]):
					invocation["foundry_id"] = entity.foundry_id
				else:
					print(f'		Unable to find invocation {invocation=}')
					self.broken_links += [f'cant find invocation {invocation["name"]}']

	def processProgression(self):
		if self.sourceClass:
			if self.force != 'none' and self.sourceClass.force:
				if self.sourceClass.force == 'none': pass
				elif self.sourceClass.force == 'arch': self.force = 'half'
				elif self.sourceClass.force == 'half': self.force = '3/4'
				elif self.sourceClass.force == '3/4': self.force = 'full'
				else: raise ValueError(self.sourceClass.force)
			if self.tech != 'none' and self.sourceClass.tech:
				if self.sourceClass.tech == 'none': pass
				elif self.sourceClass.tech == 'arch': self.tech = 'half'
				elif self.sourceClass.tech == 'half': self.tech = '3/4'
				elif self.sourceClass.tech == '3/4': self.tech = 'full'
				else: raise ValueError(self.sourceClass.tech)
			if self.superiority != '0' and self.sourceClass.superiority:
				if self.sourceClass.superiority == '0': pass
				elif self.sourceClass.superiority == '0.5': self.superiority = '1.0'
				else: raise ValueError(self.sourceClass.superiority)
		else:
			self.broken_links += ['no source class']

	def processAdvancements(self):
		for level, features in self.features.items():
			uids = [ f'Compendium.sw5e.archetypefeatures.{feature["foundry_id"]}' for feature in features.values() if "foundry_id" in feature ]
			if len(uids):
				self.advancements.append( sw5e.Advancement.ItemGrant(name="Features", uids=uids, level=level) )

	def processInvocationsText(self, importer):
		output = []
		for invocation_category, invocations in self.invocations.items():
				output += [f'<h1>{invocation_category}</h1>']
				output += ['<ul>']
				for invocation in invocations.values():
					if "foundry_id" in invocation:
						output += [f'<li>@Compendium[sw5e.invocations.{invocation["foundry_id"]}]{{{invocation["name"].capitalize()}}}</li>']
					else: self.broken_links += ['no foundry id']
				output += ['</ul>']

		self.invocationsText = "\n".join(output)

	def getImg(self, importer=None, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = utils.text.slugify(self.full_name, capitalized=capitalized)
		return f'systems/sw5e/packs/Icons/Archetypes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["name"] = self.full_name
		data["system"]["description"] = { "value": self.description }
		data["system"]["invocations"] = { "value": self.invocationsText }
		data["system"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["system"]["classIdentifier"] = utils.text.slugify(self.raw_className, capitalized=False)
		data["system"]["powercasting"] = { "force": self.force, "tech": self.tech }
		data["system"]["superiority"] = { "progression": self.superiority }
		data["system"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["system"]["source"] = self.raw_contentSource

		data["system"]["-=className"] = None
		data["system"]["-=classCasterType"] = None
		data["system"]["powercasting"]["-=progression"] = None
		data["system"]["powercasting"]["-=ability"] = None

		return [data]

	def getSubEntities(self, importer):
		sub_items = []

		for invocation_category, invocations in self.invocations.items():
			for invocation in invocations.values():
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

