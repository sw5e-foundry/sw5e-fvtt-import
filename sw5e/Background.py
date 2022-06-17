import sw5e.Entity, utils.text
import re, json

class Background(sw5e.Entity.Item):
	def load(self, raw_background):
		super().load(raw_background)


		attrs = [
			"flavorText",
			"flavorName",
			"flavorDescription",
			"flavorOptions",
			"skillProficiencies",
			"toolProficiencies",
			"languages",
			"equipment",
			"suggestedCharacteristics",
			"featureName",
			"featureText",
			"featOptions",
			"personalityTraitOptions",
			"idealOptions",
			"flawOptions",
			"bondOptions",
			"features",
			"featureRowKeys",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
			"eTag",
		]
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_background, attr))

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.flavorText = self.getFlavorText()
		self.flavorDescription = self.getFlavorDescription()
		self.flavorOptions = self.getTable(self.raw_flavorOptions, self.raw_flavorName)

		self.featOptions = self.getFeatOptions(importer)

		self.personalityTraitOptions = self.getTable(self.raw_personalityTraitOptions, 'Personality Trait')
		self.idealOptions = self.getTable(self.raw_idealOptions, 'Ideal')
		self.flawOptions = self.getTable(self.raw_flawOptions, 'Flaw')
		self.bondOptions = self.getTable(self.raw_bondOptions, 'Bond')

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Backgrounds/{name}.webp'

	def getFlavorText(self):
		text = self.raw_flavorText
		return utils.text.markdownToHtml(text)

	def getFlavorDescription(self):
		text = self.raw_flavorDescription
		if text and (match := re.search(r'\s*\|\s*d\d+\s*\|', text)):
			text = text[:match.start()]
		return utils.text.markdownToHtml(text)

	def getTable(self, table, name):
		if table:
			content = [ (
				opt["roll"],
				(opt["name"] or '') + (': ' if (opt["name"] and opt["description"]) else '') + (opt["description"] or '')
			) for opt in table ]
			header = [ f'[[/r d{len(content)} # {name}]]', name ]
			align = [ 'center', 'center' ]
			return utils.text.makeTable(content, header=header, align=align)

	def getFeatOptions(self, importer):
		if self.raw_featOptions:
			def getLink(name):
				nonlocal self
				nonlocal importer

				feat = importer.get('feat', data={'name': name})
				if feat and feat.foundry_id:
					return f'@Compendium[sw5e.feats.{feat.foundry_id}]{{{feat.name.capitalize()}}}'
				else:
					self.broken_links = True
					if self.foundry_id:
						print(f'		Unable to find feat {name=}')
					return name

			content = [ (
				opt["roll"],
				getLink(opt["name"])
			) for opt in self.raw_featOptions ]
			header = [ f'[[/r d{len(content)} # Feat]]', 'Feat' ]
			align = [ 'center', 'center' ]
			return utils.text.makeTable(content, header=header, align=align)

	def getDescription(self):
		text = \
			f'<div class="background">\n'\
			f'	<p>\n'\
			f'		{self.flavorText}\n'\
			f'	</p>\n'\
			f'</div>\n'
		if self.raw_skillProficiencies: text += \
			f'<div class="background">\n'\
			f'	<p><strong>Skill Proficiencies:</strong> {self.raw_skillProficiencies}</p>\n'\
			f'</div>\n'
		if self.raw_toolProficiencies: text += \
			f'<div class="background">\n'\
			f'	<p><strong>Tool Proficiencies:</strong> {self.raw_toolProficiencies}</p>\n'\
			f'</div>\n'
		if self.raw_languages: text += \
			f'<div class="background">\n'\
			f'	<p><strong>Languages:</strong> {self.raw_languages}</p>\n'\
			f'</div>\n'
		if self.raw_equipment: text += \
			f'<div class="background">\n'\
			f'	<p><strong>Equipment:</strong> {self.raw_equipment}</p>\n'\
			f'</div>\n'
		if self.raw_flavorName and self.flavorDescription and self.flavorOptions: text += \
			f'<div class="background"><h3>{self.raw_flavorName}</h3></div>\n'\
			f'<div class="background"><p>{self.flavorDescription}</p></div>\n'\
			f'<div class="smalltable">\n'\
			f'	<p>\n'\
			f'		{self.flavorOptions}\n'\
			f'	</p>\n'\
			f'</div>\n'
		if self.raw_featureName and self.raw_featureText: text += \
			f'<div class="background"><h2>Feature: {self.raw_featureName}</h2></div>\n'\
			f'<div class="background"><p>{self.raw_featureText}</p></div>'
		if self.featOptions: text += \
			f'<h2>Background Feat</h2>\n'\
			f'<p>\n'\
			f'	As a further embodiment of the experience and training of your background, you can choose from the\n'\
			f'	following feats:\n'\
			f'</p>\n'\
			f'<div class="smalltable">\n'\
			f'	<p>\n'\
			f'		{self.featOptions}\n'\
			f'	</p>\n'\
			f'</div>\n'
		if self.personalityTraitOptions or self.idealOptions or self.flawOptions or self.bondOptions:
			text += \
				f'<div class="background"><h2>Suggested Characteristics</h2></div>\n'
			if self.personalityTraitOptions: text += \
				f'<div class="medtable">\n'\
				f'	<p>\n'\
				f'		{self.personalityTraitOptions}\n'\
				f'	</p>\n'\
				f'</div>\n'\
				f'<p>&nbsp;</p>'
			if self.idealOptions: text += \
				f'<div class="medtable">\n'\
				f'	<p>\n'\
				f'		{self.idealOptions}\n'\
				f'	</p>\n'\
				f'</div>\n'\
				f'<p>&nbsp;</p>'
			if self.flawOptions: text += \
				f'<div class="medtable">\n'\
				f'	<p>\n'\
				f'		{self.flawOptions}\n'\
				f'	</p>\n'\
				f'</div>\n'\
				f'<p>&nbsp;</p>'
			if self.bondOptions: text += \
				f'<div class="medtable">\n'\
				f'	<p>\n'\
				f'		{self.bondOptions}\n'\
				f'	</p>\n'\
				f'</div>\n'

		return text

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription() }

		data["data"]["-=flavorText"] = None
		data["data"]["-=flavorName"] = None
		data["data"]["-=flavorDescription"] = None
		data["data"]["-=flavorOptions"] = None

		data["data"]["skillProficiencies"] = { "value": self.raw_skillProficiencies }
		data["data"]["toolProficiencies"] = { "value": self.raw_toolProficiencies }
		data["data"]["languages"] = { "value": self.raw_languages }
		data["data"]["equipment"] = { "value": self.raw_equipment }
		data["data"]["featureName"] = { "value": self.raw_featureName }
		data["data"]["featureText"] = { "value": self.raw_featureText }
		data["data"]["featOptions"] = { "value": self.raw_featOptions }

		data["data"]["-=suggestedCharacteristics"] = None
		data["data"]["-=personalityTraitOptions"] = None
		data["data"]["-=idealOptions"] = None
		data["data"]["-=flawOptions"] = None
		data["data"]["-=bondOptions"] = None

		data["data"]["source"] = self.raw_contentSource

		data["data"]["-=damage"] = None
		data["data"]["-=armorproperties"] = None
		data["data"]["-=weaponproperties"] = None

		return [data]
