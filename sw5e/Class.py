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
		self.power_casting = self.getPowerCasting()
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

	def getLevelsTable(self, importer):
		table = ['<table class="table text-center LevelTable_levelTable_14CWn">', '<thead>', '<tr>',]
		for header in self.raw_levelChangeHeaders:
			table += [f'<th align="center">{header}</th>']
		table += ['</tr>', '</thead>', '<tbody>']

		for level in range(1,21):
			table += ['<tr class="rows">']
			for header in self.raw_levelChangeHeaders:
				element = str(self.raw_levelChanges[level][header])
				if header == 'Features' and importer and not self.broken_links:
					features = utils.text.cleanStr(element).split(', ')

					for i, name in enumerate(features):
						if re.search(r'\w+ feature|—', name): continue
						if level not in self.features: continue
						if name not in self.features[level]: continue
						feature = self.features[level][name]
						features[i] = f'@Compendium[sw5e.classfeatures.{feature["foundry_id"]}]{{{feature["name"].capitalize()}}}'
					element = ', '.join(features)
				else:
					## Add inline rolls
					element = re.sub(r'\b((?:\d*d)?\d+\s*)x(\s*\d+)\b', r'\1*\2', element)
					element = re.sub(r'\b(\d*d\d+(?:\s*[+*]\s*\d+)?)\b', r'[[/r \1]]', element)
				table += [f'<td align="center">{element}</td>']
			table += ['</tr>']

		table += ['</tbody>', '</table>']

		return table

	def getPowerCasting(self):
		if self.raw_casterType == 'Tech':
			if self.raw_casterRatio == 0.0: raise ValueError("Invalid power casting progression, techcaster with 0 caster ratio.")
			if self.raw_casterRatio == 0.5: return "scout", "int"
			if self.raw_casterRatio == 0.6666666666666666: return "sentinel", "int"
			if self.raw_casterRatio == 1.0: return "engineer", "int"
		elif self.raw_casterType == 'Force':
			if self.raw_casterRatio == 0.0: raise ValueError("Invalid power casting progression, forcecaster with 0 caster ratio.")
			if self.raw_casterRatio == 0.5: return "guardian", "wis"
			if self.raw_casterRatio == 0.6666666666666666: return "sentinel", "wis"
			if self.raw_casterRatio == 1.0: return "consular", "wis"
		else: return "none", ""

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

	def getClassFeatures(self, table, importer):
		table = ['<div class="classtable">', '<blockquote>'] + table + ['</blockquote>', '</div>']

		lines =  ['&nbsp;']
		lines += ['## Class Features']
		lines += [f'As a {self.name}, you gain the following:']
		lines += ['#### Hit Points']
		lines += [f'**Hit Dice:** 1d{self.raw_hitDiceDieType} per {self.name} level']
		lines += [f'**Hit Points at 1st Level:** {self.raw_hitPointsAtFirstLevelNumber}']
		lines += [f'**Hit Points at Higher Levels:** {self.raw_hitPointsAtHigherLevelsNumber}']
		lines += ['#### Proficiencies']
		lines += [f'**Armor:** {", ".join(self.raw_armorProficiencies)}']
		lines += [f'**Weapons:** {", ".join(self.raw_weaponProficiencies)}']
		lines += [f'**Tools:** {", ".join(self.raw_toolProficiencies)}']
		lines += [f'**Saving Throws:** {", ".join(self.raw_savingThrows)}']
		lines += [f'**Skills:** {self.raw_skillChoices}']
		lines += ['**Equipment:**']
		lines += ['You start with the following equipment, in addition to the equipment granted by your background']
		#TODO: link equipments to their compendium items
		lines += self.raw_equipmentLines
		lines += ['<h3 class="mt-2">Variant: Starting Wealth</h3>']
		lines += ['In lieu of the equipment granted by your class and background, you can elect to purchase your starting gear. If you do so, you receive no equipment from your class and background, and instead roll for your starting wealthusing the criteria below:']
		lines += ['<table style="width: 300px; border: 0px;">', '<tbody>']
		lines += ['<tr>', '<td style="width: 150px;">**Class**</td>', '<td style="width: 150px;"><strong class="text-right">Funds**</td>', '</tr>']
		lines += ['<tr>', f'<td style="width: 150px;">{self.name}</td>', f'<td style="width: 150px;">{self.raw_startingWealthVariant[:-3]} cr</td>', '</tr>']
		lines += ['</tbody>', '</table>']

		return ''.join(table) + utils.text.markdownToHtml(lines)

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

	def getSkillChoices(self, importer):
		mapping = { skl["full"]: skl["abbr"] for skl in utils.config.skills }
		mapping["Any"] = 'any'
		return [ mapping[skl] for skl in self.raw_skillChoicesList ]

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["-=className"] = None

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["data"]["levels"] = 1
		data["data"]["archetype"] = ""
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
		data["data"]["powercasting"] = {
			"progression": self.power_casting[0],
			"ability": self.power_casting[1],
		}
		table = self.getLevelsTable(importer)
		data["data"]["levelsTable"] = ''.join(table)
		data["data"]["archetypes"] = ""
		data["data"]["classFeatures"] = { "value": self.getClassFeatures(table, importer) }
		data["data"]["atFlavorText"] = { "value": self.getArchetypesFlavor(importer) }

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
