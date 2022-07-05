import sw5e.Entity, sw5e.Advancement, utils.text
import re, json

class Class(sw5e.Entity.Item):
	def load(self, raw_class):
		super().load(raw_class)

		attrs = [
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
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_class, attr))
		self.raw_levelChangeHeaders = utils.text.cleanJson(raw_class, "levelChangeHeaders")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.features, self.invocations = self.getFeatures(importer)
		self.force, self.tech = self.getPowerCasting()
		self.superiority = self.getSuperiority()
		self.advancements = self.getAdvancements()

	def getDescription(self):
		out_str = f'<img style="float:right;margin:5px;border:0px" src="{self.getImg(capitalized=False, index="01")}"/>\n'
		out_str += self.raw_flavorText
		out_str += self.raw_creatingText
		out_str += '#### Quick Build\n'
		out_str += self.raw_quickBuildText

		out_str = utils.text.markdownToHtml(out_str)

		return out_str

	def getImg(self, importer=None, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = utils.text.slugify(self.name, capitalized=capitalized)
		return f'systems/sw5e/packs/Icons/Classes/{name}{index}.webp'

	def getFeatures(self, importer):
		text = self.raw_classFeatureText

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
			if match := re.match(feature_prereq_pat, subtext):
				level = match["level"]
				subtext = subtext[match.end():]

				feature_data = { "name": feature_name, "source": 'Class', "sourceName": self.name, "level": level }
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
			else:
				invocation_list = []
				for match in re.finditer(fr'{invocat_pat}(?P<text>(?:{invocat_prereq_pat})?[^#]*)', subtext):
					invocation_list.append(match.groupdict())
				invocations[feature_name] = invocation_list

		for name, invocation in invocations.items():
			if not len(invocation):
				print(invocations)
				raise ValueError(f'Invocation type "{name}" detected with no invocations.')

		return features, invocations

	def getPowerCasting(self):
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

	def getSuperiority(self):
		# TODO: Figure out how to do this without a hard coded list
		if self.name == 'Scholar': return '1'
		elif self.name == 'Fighter': return '0.5'
		return '0'

	def getAdvancements(self):
		advancements = [ sw5e.Advancement.HitPoints() ]
		for level in self.features:
			uids = []
			for name in self.features[level]:
				feature = self.features[level][name]
				uids.append(f'Compendium.sw5e.classfeatures.{feature["foundry_id"]}')
			if len(uids):
				advancements.append( sw5e.Advancement.ItemGrant(name="Features", uids=uids, level=level) )
		return advancements

	def getArchetypesFlavor(self, importer):
		output = [f'<h1>{self.raw_archetypeFlavorName}</h1>']
		output += [f'<p>{self.raw_archetypeFlavorText}</p>']

		if importer:
			output += ['<ul>']
			if importer.archetype:
				for uid in importer.archetype:
					arch = importer.archetype[uid]
					if arch.raw_className == self.name:
						if arch.foundry_id:
							output += [f'<li>@Compendium[sw5e.archetypes.{arch.foundry_id}]{{{arch.name.capitalize()}}}</li>']
						else:
							output += [f'<li>{arch.name}</li>']
			else:
				self.broken_links = True
			output += ['</ul>']

		return "\n".join(output)

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

					invocation_data["source"] = 'ClassInvocation'
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

	def getSkillChoices(self, importer):
		mapping = { skl["name"]: skl["id"] for skl in utils.config.skills }
		mapping["Any"] = 'any'
		return [ mapping[skl] for skl in self.raw_skillChoicesList ]

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["atFlavorText"] = { "value": self.getArchetypesFlavor(importer) }
		data["data"]["invocations"] = { "value": self.getInvocationsText(importer) }
		data["data"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["data"]["levels"] = 1
		data["data"]["hitDice"] = f'd{self.raw_hitDiceDieType}'
		data["data"]["hitDiceUsed"] = 0
		data["data"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["data"]["saves"] = [save[:3].lower() for save in self.raw_savingThrows]
		data["data"]["skills"] = {
			"number": self.raw_numSkillChoices,
			"choices": self.getSkillChoices(importer),
			"value": []
		}
		data["data"]["source"] = self.raw_contentSource
		data["data"]["powercasting"] = { "force": self.force, "tech": self.tech }
		data["data"]["superiority"] = { "progression": self.superiority }

		data["data"]["-=className"] = None
		data["data"]["-=archetypes"] = None
		data["data"]["-=classFeatures"] = None
		data["data"]["-=levelsTable"] = None
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

				data["source"] = 'ClassInvocation'
				data["sourceName"] = self.name
				sub_items.append((data, 'feature'))

		return sub_items
