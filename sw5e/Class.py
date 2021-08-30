import sw5e.sw5e

class Class(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		self.type = "class"

		def raw(attr): return attr and raw_item[attr]
		def clean(attr): return attr and self.cleanStr(raw_item[attr])
		def cleanJson(attr): return attr and (clean(attr+"Json") or '  ')[2:-2].split('","')

		self.summary = clean("summary")
		self.primaryAbility = clean("primaryAbility")
		self.flavorText = clean("flavorText")
		self.creatingText = clean("creatingText")
		self.quickBuildText = clean("quickBuildText")
		self.levelChangeHeaders = cleanJson("levelChangeHeaders")
		self.levelChanges = raw("levelChanges")
		self.hitDiceDieType = raw("hitDiceDieType")
		self.hitPointsAtFirstLevelNumber = raw("hitPointsAtFirstLevelNumber")
		self.hitPointsAtHigherLevelsNumber = raw("hitPointsAtHigherLevelsNumber")
		self.armorProficiencies = cleanJson("armorProficiencies")
		self.weaponProficiencies = cleanJson("weaponProficiencies")
		self.toolProficiencies = cleanJson("toolProficiencies")
		self.savingThrows = cleanJson("savingThrows")
		self.skillChoices = clean("skillChoices")
		self.numSkillChoices = raw("numSkillChoices")
		self.skillChoicesList = cleanJson("skillChoicesList")
		self.equipmentLines = cleanJson("equipmentLines")
		self.startingWealthVariant = clean("startingWealthVariant")
		self.archetypeFlavorText = clean("archetypeFlavorText")
		self.archetypeFlavorName = clean("archetypeFlavorName")
		self.imageUrls = cleanJson("imageUrls")
		self.classFeatureText = clean("classFeatureText")
		self.classFeatureText2 = raw("classFeatureText2")
		self.archetypeFlavorText = clean("archetypeFlavorText")
		self.archetypeFlavorName = clean("archetypeFlavorName")
		self.archetypes = raw("archetypes")
		self.imageUrls = cleanJson("imageUrls")
		self.casterRatio = raw("casterRatio")
		self.casterTypeEnum = raw("casterTypeEnum")
		self.powerCasting = self.getPowerCasting()
		self.casterType = clean("casterType")
		self.multiClassProficiencies = cleanJson("multiClassProficiencies")
		self.features = raw("features")
		self.featureRowKeys = raw("featureRowKeys")
		self.featureRowKeysJson = clean("featureRowKeysJson")
		self.contentTypeEnum = raw("contentTypeEnum")
		self.contentType = clean("contentType")
		self.contentSourceEnum = raw("contentSourceEnum")
		self.contentSource = clean("contentSource")
		self.partitionKey = clean("partitionKey")
		self.rowKey = clean("rowKey")

	def getDescription(self):
		out_str = f'<img style="float:right;margin:5px;border:0px" src="{self.getImg(capitalized=False, index="01")}"/>\n'
		out_str += self.flavorText
		out_str += self.creatingText
		out_str += '#### Quick Build\n'
		out_str += self.quickBuildText

		out_str = self.markdownToHtml(out_str)

		return out_str

	def getImg(self, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = self.name if capitalized else self.name.lower()
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
					features = self.cleanStr(element).split(', ')
					for i in range(len(features)):
						feature = importer.get('feature', name=features[i], class_name=self.name, level=level)
						if feature:
							if feature.id:
								features[i] = f'@Compendium[sw5e.classFeatures.{feature.id}{{{feature.name.capitalize()}}}]'
						else:
							self.brokenLinks = True
					element = ', '.join(features)
				table += [f'<td align="center">{element}</td>']
			table += ['</tr>']

		table += ['</tbody>', '</table>']

		return table

	def getPowerCasting(self):
		if self.casterTypeEnum == 0: return "none", ""
		if self.casterTypeEnum == 1:
			if self.casterRatio == 0.0: raise ValueError("Invalid power casting progression, techcaster with 0 caster ratio.")
			if self.casterRatio == 0.5: return "scout", "int"
			if self.casterRatio == 0.6666666666666666: return "sentinel", "int"
			if self.casterRatio == 1.0: return "engineer", "int"
		if self.casterTypeEnum == 2:
			if self.casterRatio == 0.0: raise ValueError("Invalid power casting progression, forcecaster with 0 caster ratio.")
			if self.casterRatio == 0.5: return "guardian", "wis"
			if self.casterRatio == 0.6666666666666666: return "sentinel", "wis"
			if self.casterRatio == 1.0: return "consular", "wis"

	def getFeatures(self, table, importer):
		table = ['<div class="classtable">', '<blockquote>'] + table + ['</blockquote>', '</div>']

		lines =  ['&nbsp;']
		lines += ['## Class Features']
		lines += [f'As a {self.name}, you gain the following class features.']
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
		lines += ['<tr>', f'<td style="width: 150px;">{self.name}</td>', f'<td style="width: 150px;">[[/r {self.startingWealthVariant[:-3]}]] cr</td>', '</tr>']
		lines += ['</tbody>', '</table>']

		return self.markdownToHtml(lines)

	def getArchetypesFlavor(self, importer):
		output = [f'<h1>{self.archetypeFlavorName}</h1>']
		output += [f'<p>{self.archetypeFlavorText}</p>']

		if importer:
			output += ['<ul>']
			if importer.archetype:
				for arch in importer.archetype:
					if arch.className == self.name:
						if arch.id:
							output += [f'<li>@Compendium[sw5e.archetypes.{arch.id}]{{{arch.name.capitalize()}}}</li>']
						else:
							output += [f'<li>{arch.name}</li>']
			else:
				self.brokenLinks = True
			output += ['</ul>']

		return "\n".join(output)

	def getData(self, importer):
		data = super().getData(importer)
		data["type"] = self.type
		data["img"] = self.getImg()
		data["data"] = {}
		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["className"] = self.name
		data["data"]["levels"] = 1
		data["data"]["archetype"] = ""
		data["data"]["hitDice"] = self.hitDiceDieType
		data["data"]["hitDiceUsed"] = 0
		data["data"]["saves"] = [save[:3].lower() for save in self.savingThrows]
		data["data"]["skills"] = {
			"number": self.numSkillChoices,
			"choices": self.skillChoicesList,
			"value": []
		}
		data["data"]["source"] = self.contentSource
		data["data"]["powerCasting"] = {
			"progression": self.powerCasting[0],
			"ability": self.powerCasting[1],
		}
		table = self.getLevelsTable(importer)
		data["data"]["levelsTable"] = ''.join(table)
		data["data"]["archetypes"] = ""
		data["data"]["classFeatures"] = { "value": self.getFeatures(table, importer) }
		data["data"]["atFlavorText"] = { "value": self.getArchetypesFlavor(importer) }
		return data
