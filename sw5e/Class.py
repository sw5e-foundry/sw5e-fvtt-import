import sw5e.Entity, sw5e.Advancement, utils.text
import re, json

class Class(sw5e.Entity.Item):
	def getAttrs(self):
		return super().getAttrs() + [
			"summary",
			"primaryAbility",
			"flavorText",
			"creatingText",
			"quickBuildText",
			"levelChanges",
			"hitDiceDieTypeEnum",
			"hitDiceDieType",
			"hitPointsAtFirstLevel",
			"hitPointsAtHigherLevels",
			"hitPointsAtFirstLevelNumber",
			"hitPointsAtHigherLevelsNumber",
			"armorProficiencies",
			"weaponProficiencies",
			"toolProficiencies",
			"toolProficienciesList",
			"savingThrows",
			"skillChoices",
			"numSkillChoices",
			"skillChoicesList",
			"equipmentLines",
			"startingWealthVariant",
			"classFeatureText",
			"classFeatureText2",
			"archetypeFlavorText",
			"archetypeFlavorName",
			"archetypes",
			"imageUrls",
			"casterRatio",
			"casterTypeEnum",
			"casterType",
			"multiClassProficiencies",
			"features",
			"featureRowKeys",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
			"timestamp",
			"eTag",
		]

	def getJsonAttrs(self):
		return super().getJsonAttrs() + [ "levelChangeHeaders" ]

	def load(self, raw_class):
		super().load(raw_class)

		self.description = self.loadDescription()
		self.features, self.invocations, self.asi = self.loadFeatures()
		self.force, self.tech = self.loadPowerCasting()
		self.superiority = self.loadSuperiority()
		self.formulas = self.loadFormulas()
		self.armorProficiencies = self.loadArmorProficiencies()
		self.weaponProficiencies = self.loadWeaponProficiencies()
		self.toolProficiencies = self.loadToolProficiencies()
		self.skillChoices = self.loadSkillChoices()
		self.multiclassProficiencies = self.loadMulticlassProficiencies()
		self.advancements = self.loadAdvancements()
		self.archetypes = []
		self.archetypesFlavor = ""
		self.invocationsText = ""

	def loadDescription(self):
		out_str = f'<img style="float:right;margin:5px;border:0px" src="{self.getImg(capitalized=False, index="01")}"/>\n'
		out_str += self.raw_flavorText
		out_str += self.raw_creatingText
		out_str += '#### Quick Build\n'
		out_str += self.raw_quickBuildText

		out_str = utils.text.markdownToHtml(out_str)

		return out_str

	def loadFeatures(self):
		text = self.raw_classFeatureText

		features = {}
		invocations = {}
		asi = []

		not_a_feature = '|'.join(("GM Consideration",))
		class_name = '|'.join((name.replace('([()])', '\\\1') for name in (self.name, )))

		it = utils.text.exactly_x_times(r'[_*]', 1)
		b = utils.text.exactly_x_times(r'[_*]', 2)
		ib = utils.text.exactly_x_times(r'[_*]', 3)
		h3 = utils.text.exactly_x_times(r'#', 3)
		h4 = utils.text.exactly_x_times(r'#', 4)

		levels_pat = fr'(?P<levels>(?P<level>\d+)\w+(?:, \d+\w+|,? and \d+\w+)*) level'
		feature_pat = fr'{h3} (?!{not_a_feature})(?P<name>[^\n]*)\s*';
		feature_prereq_pat = fr'{ib}{self.name}:{b} {levels_pat}{it}\s*';
		invocat_pat = fr'{h4} (?!{not_a_feature})(?P<name>[^\n]*)\s*';
		invocat_prereq_pat = fr'{ib}Prerequisite:{b} (?:{levels_pat})?(?:, )?(?P<prerequisite>[^\n]*){it}\s*';
		for match in re.finditer(feature_pat, text):
			feature_name = match["name"]
			subtext = text[match.end():]
			if (next_feature := re.search(feature_pat, subtext)): subtext = subtext[:next_feature.start()]

			# ASI are not added as normal features
			if feature_name.strip().lower() == "ability score improvement":
				match = re.match(feature_prereq_pat, subtext)
				levels = match["levels"]
				for match in re.finditer(fr'\d+', levels):
					level = match[0]
					asi.append(int(level))

			# If there is a prerequisite, it's a normal feature
			elif match := re.match(feature_prereq_pat, subtext):
				level = match["level"]
				subtext = subtext[match.end():]

				feature_data = {
					"name": feature_name,
					"source": 'Class',
					"sourceName": self.name,
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
				invocation_category = feature_name
				if invocation_category not in invocations: invocations[invocation_category] = {}
				for match in re.finditer(fr'{invocat_pat}(?P<text>(?:{invocat_prereq_pat})?[^#]*)', subtext):
					invocation_name = match["name"]
					level = match["level"]
					text = match["text"]

					invocation_data = {
						"name": invocation_name,
						"text": text,
						"level": int(level) if level else None,
						"prerequisite": match["prerequisite"],
						"source": 'ClassInvocation',
						"sourceName": self.name,
					}

					invocations[invocation_category][invocation_name] = {
						"name": invocation_name,
						"level": level,
						"text": text,
						"prerequisite": match["prerequisite"],
						"uid": self.getUID(invocation_data, 'Feature'),
					}

		for name, invocation in invocations.items():
			if not len(invocation):
				print(json.dumps(invocations, indent=4, sort_keys=False, ensure_ascii=False))
				raise ValueError(f'Invocation type "{name}" detected with no invocations.')

		return features, invocations, asi

	def loadPowerCasting(self):
		mapping = {
			# [0.0]: 'none',
			0.25: 'arch',
			0.5: 'half',
			0.6666666666666666: '3/4',
			1: 'full'
		}
		(cType, cRatio) = (self.raw_casterType, self.raw_casterRatio)

		if cType == 'None': return 'none', 'none'

		if cRatio in mapping:
			if cType == 'Tech': return 'none', mapping[cRatio]
			elif cType == 'Force': return mapping[cRatio], 'none'

		raise ValueError(f'Invalid power casting progression, {cType}caster with {cRatio} caster ratio.')

	def loadSuperiority(self):
		# TODO: Figure out how to do this without a hard coded list
		if self.name == 'Scholar': return '1'
		elif self.name == 'Fighter': return '0.5'
		return '0'

	def loadFormulas(self):
		formulas = {}
		nope = [
			'level',
			'proficiency bonus',
			'features',
			'force points',
			'force powers known',
			'tech points',
			'tech powers known',
			'max power level',
			'combat superiority',
			'maneuvers known',
			'superiority dice',
		]

		for name in self.raw_levelChangeHeaders:
			if name.lower() in nope: continue
			formulas[name] = { "name": name, "values": {} }

		for lvl, data in self.raw_levelChanges.items():
			for name, value in data.items():
				if name in formulas:
					formulas[name]["values"][lvl] = value

		return formulas

	def loadArmorProficiencies(self):
		mapping = { arm["name"].lower(): [ arm["id"] ] for arm in utils.config.armor_types }
		mapping["none"] = []
		mapping["all"] = [ arm["id"] for arm in utils.config.armor_types ]
		return [ armor for armors in self.raw_armorProficiencies for armor in mapping[armors.lower().split(" ")[0]]]

	def loadWeaponProficiencies(self):
		grants = []
		# TODO: make this respect weapon property restrictions
		for wpn in self.raw_weaponProficiencies:
			wpn = wpn.lower()
			if wpn.startswith('all'): wpn = ' '.join(wpn.split(' ')[1:])
			fchoices, fgrants = utils.text.getTraits(wpn, self.name, require_prefix=False, restrict_types=['weapons'])
			if fchoices:
				for fchoice in fchoices: fchoice["pool"] = [ trait[:-2] if trait.endswith(':*') else trait for trait in fchoice["pool"] ]
				grants.extend(fchoice["pool"])
			if fgrants: grants.extend(fgrants)

		return grants

	def loadToolProficiencies(self):
		# TODO: make this respect weapon property restrictions
		tool_mapping = { tool["name"]: tool["id"] for tool in utils.config.tools }
		generic_mapping = {
			"none": None,
			"any one": "*",
			"one of your choice": "*",
			"one specialist's kit of your choice": "specialist:*",
		}

		choices, grants = [], []

		for tool in self.raw_toolProficiencies:
			tool = tool.lower()
			if tool_id := tool_mapping.get(tool):
				grants.append(f'tool:{tool_mapping[tool]}')
			elif tool_id := generic_mapping.get(tool):
				choices.append({
					"count": 1,
					"pool": [ f'tool:{tool_id}' ]
				})

		return { "choices": choices, "grants": grants }

	def loadSkillChoices(self):
		mapping = { skl["name"].lower(): f'skills:{skl["id"]}' for skl in utils.config.skills }
		mapping["any"] = 'skills:*'
		return [ mapping[skl.lower()] for skl in self.raw_skillChoicesList ]

	def loadMulticlassProficiencies(self):
		grants = []
		for prof in self.raw_multiClassProficiencies:
			prof = prof.lower()
			if prof.startswith('all'): prof = ' '.join(prof.split(' ')[1:])
			fchoices, fgrants = utils.text.getTraits(prof, self.name, require_prefix=False)
			if fchoices:
				for fchoice in fchoices: fchoice["pool"] = [ trait[:-2] if trait.endswith(':*') else trait for trait in fchoice["pool"] ]
				grants.extend(fchoice["pool"])
			if fgrants: grants.extend(fgrants)

		return grants

	def loadAdvancements(self):
		advancements = [ sw5e.Advancement.HitPoints() ]

		for formula in self.formulas.values():
			advancements.append( sw5e.Advancement.ScaleValue(name=formula["name"], values=formula["values"]) )

		for level in self.asi:
			advancements.append( sw5e.Advancement.AbilityScoreImprovement(level=level) )

		if self.armorProficiencies:
			advancements.append( sw5e.Advancement.Trait(level=1, grants=[
				f'armor:{arm}' for arm in self.armorProficiencies
			], class_restriction='primary') )

		if self.weaponProficiencies:
			advancements.append( sw5e.Advancement.Trait(level=1, grants=self.weaponProficiencies, class_restriction='primary') )

		if self.toolProficiencies["choices"] or self.toolProficiencies["grants"]:
			advancements.append( sw5e.Advancement.Trait(level=1, 
				grants=self.toolProficiencies["grants"],
				choices=self.toolProficiencies["choices"],
				class_restriction='primary'
			) )

		if self.raw_savingThrows:
			advancements.append( sw5e.Advancement.Trait(level=1, grants=[
				f'saves:{save.lower()[:3]}' for save in self.raw_savingThrows
			], class_restriction='primary') )

		if self.skillChoices:
			advancements.append( sw5e.Advancement.Trait(level=1, choices=[{
				"count": self.raw_numSkillChoices,
				"pool": self.skillChoices,
			}], allow_replacements=True, class_restriction='primary') )

		if self.multiclassProficiencies:
			advancements.append( sw5e.Advancement.Trait(name='Multiclass Proficiencies',level=1, grants=self.multiclassProficiencies, class_restriction='secondary') )

		return advancements



	def process(self, importer):
		super().process(importer)

		if importer:
			self.processFeatures(importer)
			self.processArchetypes(importer)
			self.processArchetypesFlavor(importer)
			self.processInvocationsText(importer)
			self.processAdvancements()
		else:
			self.broken_links += ['no importer']

	def processFeatures(self, importer):
		all_features = {}
		for level, features in self.features.items():
			for feature in features.values():
				if entity := importer.get('feature', uid=feature["uid"]):
					feature["foundry_id"] = entity.foundry_id
					feature["traits"] = entity.traits
				else:
					print(f'		Unable to find feature {feature=}')
					self.broken_links += [f'cant find feature {feature["name"]}']
				all_features[feature["name"]] = feature

		for invocation_category, invocations in self.invocations.items():
			for name, invocation in invocations.items():
				if name.startswith('_'): continue
				if entity := importer.get('feature', uid=invocation["uid"]):
					invocation["foundry_id"] = entity.foundry_id
				else:
					print(f'		Unable to find invocation {invocation=}')
					self.broken_links += [f'cant find invocation {invocation["name"]}']

			attempts = [
				invocation_category,
				*utils.text.getSingular(invocation_category),
				" ".join(invocation_category.split()[1:]),
				*utils.text.getSingular(" ".join(invocation_category.split()[1:])),
			]
			try:
				feature_name = [ attempt for attempt in attempts if attempt in all_features ][0]
			except:
				print("Mismatched Invocation Category", invocation_category, all_features.keys(), attempts)
				raise

			invocations["_feature_name"] = feature_name
			invocations["_text"] = all_features[feature_name]["description"]

	def processArchetypes(self, importer):
		if importer.archetype:
			self.archetypes = [
				{ "uuid": uuid, "name": arch.full_name, "fid": arch.foundry_id}
				for uuid, arch in importer.archetype.items()
				if arch.raw_className == self.name
			]
		else: broken_links += [ "no archetypes" ]

	def processArchetypesFlavor(self, importer):
		output = [f'<h1>{self.raw_archetypeFlavorName}</h1>']
		output += [f'<p>{self.raw_archetypeFlavorText}</p>']

		if len(self.archetypes) > 0:
			output += ['<ul>']
			output += [f'<li>@Compendium[sw5e.archetypes.{arch["fid"]}]{{{arch["name"].capitalize()}}}</li>' for arch in self.archetypes]
			output += ['</ul>']

		self.archetypesFlavor = "\n".join(output)

	def processInvocationsText(self, importer):
		output = []
		for invocation_category, invocations in self.invocations.items():
			output += [f'<h1>{invocation_category}</h1>']
			output += ['<ul>']
			for name, invocation in invocations.items():
				if name.startswith('_'): continue
				if "foundry_id" in invocation:
					output += [f'<li>@Compendium[sw5e.invocations.{invocation["foundry_id"]}]{{{invocation["name"].capitalize()}}}</li>']
				else: self.broken_links += ['no foundry id']
			output += ['</ul>']

		self.invocationsText = "\n".join(output)

	def processAdvancements(self):
		# Grant Features
		for level, features in self.features.items():
			uids = []
			for name, feature in features.items():
				if 'foundry_id' in feature: uids.append(f'Compendium.sw5e.classfeatures.{feature["foundry_id"]}')
				else: self.broken_links += [f'missing foundry_id for {feature["name"]}']
			if len(uids):
				self.advancements.append( sw5e.Advancement.ItemGrant(name="Features", uids=uids, level=level) )

		# Feature Traits
		for level, features in self.features.items():
			for name, feature in features.items():
				choices, grants = feature["traits"]
				if choices or grants:
					self.advancements.append( sw5e.Advancement.Trait(level=level, choices=choices, grants=grants) )

		# Choose Invocations
		for invocation_category, invocations in self.invocations.items():
			# Prepare the pool of invocations
			uids = []
			for name, invocation in invocations.items():
				if name.startswith('_'): continue
				# TODO: Once 'ItemChoice' supports levels, change this to use it
				if 'foundry_id' in invocation: uids.append(f'Compendium.sw5e.invocations.{invocation["foundry_id"]}')
				else: self.broken_links += [f'missing foundry_id for {invocation["name"]}']

			# Determine the header row used for the choices
			feature_name = invocations["_feature_name"]
			attempts = [
				feature_name,
				f'{feature_name} Options',
				f'{" ".join(feature_name.split()[1:])} Slots',
				invocation_category,
				f'{" ".join(invocation_category.split()[1:])}',
				f'{" ".join(invocation_category.split()[1:])} Known',
			]
			try:
				header = [ attempt for attempt in attempts if attempt in self.raw_levelChangeHeaders ][0]
			except:
				print("Mismatched Invocation Category", invocation_category, self.raw_levelChangeHeaders, attempts)
				raise

			# Prepare the choices
			choices = {}
			previous = 0
			for level, changes in self.raw_levelChanges.items():
				cur = changes[header]
				if type(cur) == str: cur = int(cur) if cur.isnumeric() else 0
				if cur > previous:
					choices[level] = cur - previous
					previous = cur

			# Create the advancement
			self.advancements.append( sw5e.Advancement.ItemChoice(
				name=invocation_category,
				hint=invocations.get("_text", ''),
				choices=choices,
				item_type='feat',
				pool=uids,
				restriction_type='class',
				restriction_subtype=f'{self.name.lower()}Invocation'
			) )

		# Choose Archetype
		if len(self.archetypes) > 0:
			# Prepare the pool of archetypes
			uids = [ f'Compendium.sw5e.archetypes.{arch["fid"]}' for arch in self.archetypes ]

			# Prepare the choices
			choices = { "3": 1 }

			# Create the advancement
			self.advancements.append( sw5e.Advancement.ItemChoice(
				name=self.raw_archetypeFlavorName,
				hint=self.raw_archetypeFlavorText,
				choices=choices,
				item_type='archetype',
				pool=uids,
			) )



	def getImg(self, importer=None, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = utils.text.slugify(self.name, capitalized=capitalized)
		name = re.sub(f'-Depreciated', '', name)
		return f'systems/sw5e/packs/Icons/Classes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.description }
		data["system"]["atFlavorText"] = { "value": self.archetypesFlavor }
		data["system"]["invocations"] = { "value": self.invocationsText }
		data["system"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["system"]["levels"] = 1
		data["system"]["hitDice"] = f'd{self.raw_hitDiceDieType}'
		data["system"]["hitDiceUsed"] = 0
		data["system"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["system"]["source"] = { "custom": self.raw_contentSource }
		data["system"]["powercasting"] = { "force": self.force, "tech": self.tech }
		data["system"]["superiority"] = { "progression": self.superiority }

		data["system"]["-=className"] = None
		data["system"]["-=archetypes"] = None
		data["system"]["-=classFeatures"] = None
		data["system"]["-=levelsTable"] = None
		data["system"]["powercasting"]["-=progression"] = None
		data["system"]["powercasting"]["-=ability"] = None

		return [data]

	def getSubEntities(self, importer):
		sub_items = []

		for invocation_category, invocations in self.invocations.items():
			for name, invocation in invocations.items():
				if name.startswith('_'): continue
				data = {}

				for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
					data[key] = getattr(self, f'raw_{key}')

				data["name"] = invocation["name"]
				data["text"] = invocation["text"]
				data["level"] = int(invocation["level"]) if invocation["level"] else None
				data["prerequisite"] = invocation["prerequisite"]

				data["source"] = 'ClassInvocation'
				data["sourceName"] = self.name
				sub_items.append((data, 'feature'))

		return sub_items


