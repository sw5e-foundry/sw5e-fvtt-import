import sw5e.Entity, utils.text
import re, json

class Class(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.summary = utils.text.clean(raw_item, "summary")
		self.primaryAbility = utils.text.clean(raw_item, "primaryAbility")
		self.flavorText = utils.text.clean(raw_item, "flavorText")
		self.creatingText = utils.text.clean(raw_item, "creatingText")
		self.quickBuildText = utils.text.clean(raw_item, "quickBuildText")
		self.levelChangeHeaders = utils.text.cleanJson(raw_item, "levelChangeHeaders")
		self.levelChanges = utils.text.cleanJson(raw_item, "levelChanges")
		self.hitDiceDieTypeEnum = utils.text.raw(raw_item, "hitDiceDieTypeEnum")
		self.hitDiceDieType = utils.text.raw(raw_item, "hitDiceDieType")
		self.hitPointsAtFirstLevel = utils.text.clean(raw_item, "hitPointsAtFirstLevel")
		self.hitPointsAtHigherLevels = utils.text.clean(raw_item, "hitPointsAtHigherLevels")
		self.hitPointsAtFirstLevelNumber = utils.text.raw(raw_item, "hitPointsAtFirstLevelNumber")
		self.hitPointsAtHigherLevelsNumber = utils.text.raw(raw_item, "hitPointsAtHigherLevelsNumber")
		self.armorProficiencies = utils.text.cleanJson(raw_item, "armorProficiencies")
		self.weaponProficiencies = utils.text.cleanJson(raw_item, "weaponProficiencies")
		self.toolProficiencies = utils.text.cleanJson(raw_item, "toolProficiencies")
		self.toolProficienciesList = utils.text.cleanJson(raw_item, "toolProficienciesList")
		self.savingThrows = utils.text.cleanJson(raw_item, "savingThrows")
		self.skillChoices = utils.text.clean(raw_item, "skillChoices")
		self.numSkillChoices = utils.text.raw(raw_item, "numSkillChoices")
		self.skillChoicesList = utils.text.cleanJson(raw_item, "skillChoicesList")
		self.equipmentLines = utils.text.cleanJson(raw_item, "equipmentLines")
		self.startingWealthVariant = utils.text.clean(raw_item, "startingWealthVariant")
		self.classFeatureText = utils.text.clean(raw_item, "classFeatureText")
		self.classFeatureText2 = utils.text.clean(raw_item, "classFeatureText2")
		self.archetypeFlavorText = utils.text.clean(raw_item, "archetypeFlavorText")
		self.archetypeFlavorName = utils.text.clean(raw_item, "archetypeFlavorName")
		self.archetypes = utils.text.clean(raw_item, "archetypes")
		self.imageUrls = utils.text.cleanJson(raw_item, "imageUrls")
		self.casterRatio = utils.text.raw(raw_item, "casterRatio")
		self.casterTypeEnum = utils.text.raw(raw_item, "casterTypeEnum")
		self.casterType = utils.text.clean(raw_item, "casterType")
		self.multiClassProficiencies = utils.text.cleanJson(raw_item, "multiClassProficiencies")
		self.features = utils.text.clean(raw_item, "features")
		self.featureRowKeys = utils.text.cleanJson(raw_item, "featureRowKeys")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.power_casting = self.getPowerCasting()
		self.sub_item_features = self.getSubItemFeatures()

	def getDescription(self):
		out_str = f'<img style="float:right;margin:5px;border:0px" src="{self.getImg(capitalized=False, index="01")}"/>\n'
		out_str += self.flavorText
		out_str += self.creatingText
		out_str += '#### Quick Build\n'
		out_str += self.quickBuildText

		out_str = utils.text.markdownToHtml(out_str)

		return out_str

	def getImg(self, importer=None, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = self.name if capitalized else self.name.lower()
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Classes/{name}{index}.webp'

	def getLevelsTable(self, importer):
		table = ['<table class="table text-center LevelTable_levelTable_14CWn">', '<thead>', '<tr>',]
		for header in self.levelChangeHeaders:
			table += [f'<th align="center">{header}</th>']
		table += ['</tr>', '</thead>', '<tbody>']

		for level in range(1,21):
			table += ['<tr class="rows">']
			for header in self.levelChangeHeaders:
				element = self.levelChanges[str(level)][header]
				if header == 'Features' and importer:
					features = utils.text.cleanStr(element).split(', ')
					for i in range(len(features)):
						if not re.search(r'\w+ feature|—', features[i]):
							feature_data = {
								"name": features[i],
								"source": 'Class',
								"sourceName": self.name,
								"level": level
							}
							if features[i] != 'Ability Score Improvement':
								feature_data["name"] = re.sub(r'(.*?) (?:\(.*?\)|Improvement)', r'\1', features[i])

							feature = importer.get('feature', data=feature_data)
							if feature and feature.foundry_id:
									features[i] = f'@Compendium[sw5e.classfeatures.{feature.foundry_id}]{{{feature.name.capitalize()}}}'
							else:
								self.broken_links = True
								if self.foundry_id and not feature:
									print(f'		Unable to find feature {feature_data=}')
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
		if self.casterType == 'Tech':
			if self.casterRatio == 0.0: raise ValueError("Invalid power casting progression, techcaster with 0 caster ratio.")
			if self.casterRatio == 0.5: return "scout", "int"
			if self.casterRatio == 0.6666666666666666: return "sentinel", "int"
			if self.casterRatio == 1.0: return "engineer", "int"
		elif self.casterType == 'Force':
			if self.casterRatio == 0.0: raise ValueError("Invalid power casting progression, forcecaster with 0 caster ratio.")
			if self.casterRatio == 0.5: return "guardian", "wis"
			if self.casterRatio == 0.6666666666666666: return "sentinel", "wis"
			if self.casterRatio == 1.0: return "consular", "wis"
		else: return "none", ""

	def getSubItemFeatures(self):
		text = self.classFeatureText

		features = {}
		for match in re.finditer(r'\s### (?P<name>[^\n]*)\n(?!\s*_\*\*' + self.name + ')', text):
			text = text[match.start():]
			feature = []

			pattern = r'#### (?P<name>[^\n]*)\n'
			pattern += r'(?P<text>'
			pattern += r'(?:\s*_\*\*Prerequisite:\*\* (?P<level>\d+)\w+(?:, \d+\w+| and \d+\w+)* level)?'
			pattern += r'[^#]*)(?:\n|$)'

			for invocation in re.finditer(pattern, text):
				feature.append({
					"name": invocation["name"],
					"text": invocation["text"],
					"level": int(invocation["level"]) if invocation["level"] else None,
				})

			features[match["name"]] = feature

		return features

	def getFeatures(self, table, importer):
		table = ['<div class="classtable">', '<blockquote>'] + table + ['</blockquote>', '</div>']

		lines =  ['&nbsp;']
		lines += ['## Class Features']
		lines += [f'As a {self.name}, you gain the following:']
		lines += ['#### Hit Points']
		lines += [f'**Hit Dice:** 1d{self.hitDiceDieType} per {self.name} level']
		lines += [f'**Hit Points at 1st Level:** {self.hitPointsAtFirstLevelNumber}']
		lines += [f'**Hit Points at Higher Levels:** {self.hitPointsAtHigherLevelsNumber}']
		lines += ['#### Proficiencies']
		lines += [f'**Armor:** {", ".join(self.armorProficiencies)}']
		lines += [f'**Weapons:** {", ".join(self.weaponProficiencies)}']
		lines += [f'**Tools:** {", ".join(self.toolProficiencies)}']
		lines += [f'**Saving Throws:** {", ".join(self.savingThrows)}']
		lines += [f'**Skills:** {self.skillChoices}']
		lines += ['**Equipment:**']
		lines += ['You start with the following equipment, in addition to the equipment granted by your background']
		#TODO: link equipments to their compendium items
		lines += self.equipmentLines
		lines += ['<h3 class="mt-2">Variant: Starting Wealth</h3>']
		lines += ['In lieu of the equipment granted by your class and background, you can elect to purchase your starting gear. If you do so, you receive no equipment from your class and background, and instead roll for your starting wealthusing the criteria below:']
		lines += ['<table style="width: 300px; border: 0px;">', '<tbody>']
		lines += ['<tr>', '<td style="width: 150px;">**Class**</td>', '<td style="width: 150px;"><strong class="text-right">Funds**</td>', '</tr>']
		lines += ['<tr>', f'<td style="width: 150px;">{self.name}</td>', f'<td style="width: 150px;">{self.startingWealthVariant[:-3]} cr</td>', '</tr>']
		lines += ['</tbody>', '</table>']

		return ''.join(table) + utils.text.markdownToHtml(lines)

	def getArchetypesFlavor(self, importer):
		output = [f'<h1>{self.archetypeFlavorName}</h1>']
		output += [f'<p>{self.archetypeFlavorText}</p>']

		if importer:
			output += ['<ul>']
			if importer.archetype:
				for uid in importer.archetype:
					arch = importer.archetype[uid]
					if arch.className == self.name:
						if arch.foundry_id:
							output += [f'<li>@Compendium[sw5e.archetypes.{arch.foundry_id}]{{{arch.name.capitalize()}}}</li>']
						else:
							output += [f'<li>{arch.name}</li>']
			else:
				self.broken_links = True
			output += ['</ul>']

		return "\n".join(output)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["className"] = self.name
		data["data"]["levels"] = 1
		data["data"]["archetype"] = ""
		data["data"]["hitDice"] = f'd{self.hitDiceDieType}'
		data["data"]["hitDiceUsed"] = 0
		data["data"]["saves"] = [save[:3].lower() for save in self.savingThrows]
		data["data"]["skills"] = {
			"number": self.numSkillChoices,
			"choices": self.skillChoicesList,
			"value": []
		}
		data["data"]["source"] = self.contentSource
		data["data"]["powercasting"] = {
			"progression": self.power_casting[0],
			"ability": self.power_casting[1],
		}
		table = self.getLevelsTable(importer)
		data["data"]["levelsTable"] = ''.join(table)
		data["data"]["archetypes"] = ""
		data["data"]["classFeatures"] = { "value": self.getFeatures(table, importer) }
		data["data"]["atFlavorText"] = { "value": self.getArchetypesFlavor(importer) }

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

				data["source"] = 'ClassInvocation'
				data["sourceName"] = self.name
				sub_items.append((data, 'feature'))

		return sub_items
