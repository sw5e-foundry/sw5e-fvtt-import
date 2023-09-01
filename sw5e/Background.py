import sw5e.Entity, utils.text
import re, json

class Background(sw5e.Entity.Item):
	def getAttrs(self):
		return super().getAttrs() + [
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

	def load(self, raw_background):
		super().load(raw_background)

		self.flavorText = self.loadFlavorText()
		self.flavorDescription = self.loadFlavorDescription()
		self.flavorOptions = utils.text.makeRollTable(self.raw_flavorOptions, self.raw_flavorName)
		self.personalityTraitOptions = utils.text.makeRollTable(self.raw_personalityTraitOptions, 'Personality Trait')
		self.idealOptions = utils.text.makeRollTable(self.raw_idealOptions, 'Ideal')
		self.flawOptions = utils.text.makeRollTable(self.raw_flawOptions, 'Flaw')
		self.bondOptions = utils.text.makeRollTable(self.raw_bondOptions, 'Bond')

		self.featOptions = self.loadFeatOptions()
		self.advancements = self.loadAdvancements()

	def loadFlavorText(self):
		text = self.raw_flavorText
		return utils.text.markdownToHtml(text)

	def loadFlavorDescription(self):
		text = self.raw_flavorDescription
		if text and (match := re.search(r'\s*\|\s*d\d+\s*\|', text)):
			text = text[:match.start()]
		return utils.text.markdownToHtml(text)

	def loadFeatOptions(self):
		feats = []

		for feat_data in (self.raw_featOptions or []):
			feat = {
				"name": feat_data["name"],
				"roll": feat_data["roll"],
			}
			feat["uid"] = self.getUID(feat, 'Feat')
			feats.append(feat)

		return feats

	def loadAdvancements(self):
		advancements = []
		return advancements

	def process(self, importer):
		super().process(importer)

		self.processFeatOptions(importer)
		self.processAdvancements()

		self.featOptionsText = self.getFeatOptionsText()

	def processFeatOptions(self, importer):
		for feat in self.featOptions:
			if entity := importer.get('feat', uid=feat["uid"]):
				feat["foundry_id"] = entity.foundry_id
			else:
				print(f'		Unable to find {feat=}')
				self.broken_links += [f'cant find feat {feat["name"]}']

	def processAdvancements(self):
		# Choose Feat
		if len(self.featOptions) > 0:
			# Prepare the pool of archetypes
			uids = [ f'Compendium.sw5e.feats.{feat["foundry_id"]}' for feat in self.featOptions ]

			# Prepare the choices
			choices = { "0": 1 }

			# Create the advancement
			self.advancements.append( sw5e.Advancement.ItemChoice(
				name='Feat',
				hint='These feats are only suggestions, you can choose any feat without a level prerequisite, provided you meet any other prerequisite.',
				choices=choices,
				item_type='feat',
				restriction_type='feat',
				pool=uids,
			) )

	def getFeatOptionsText(self):
		def getLink(feat):
			return f'@Compendium[sw5e.feats.{feat.get("foundry_id", None)}]{{{feat["name"].capitalize()}}}'

		content = [ (
			opt["roll"],
			getLink(opt)
		) for opt in self.featOptions ]
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
		if self.featOptionsText: text += \
			f'<h2>Background Feat</h2>\n'\
			f'<p>\n'\
			f'	As a further embodiment of the experience and training of your background, you can choose from the\n'\
			f'	following feats:\n'\
			f'</p>\n'\
			f'<div class="smalltable">\n'\
			f'	<p>\n'\
			f'		{self.featOptionsText}\n'\
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

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Backgrounds/{name}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription() }

		data["system"]["skillProficiencies"] = { "value": self.raw_skillProficiencies }
		data["system"]["toolProficiencies"] = { "value": self.raw_toolProficiencies }
		data["system"]["languages"] = { "value": self.raw_languages }
		data["system"]["equipment"] = { "value": self.raw_equipment }
		data["system"]["featureName"] = { "value": self.raw_featureName }
		data["system"]["featureText"] = { "value": self.raw_featureText }
		data["system"]["featOptions"] = { "value": self.raw_featOptions }
		data["system"]["source"] = self.raw_contentSource
		data["system"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]

		data["system"]["-=flavorText"] = None
		data["system"]["-=flavorName"] = None
		data["system"]["-=flavorDescription"] = None
		data["system"]["-=flavorOptions"] = None

		data["system"]["-=suggestedCharacteristics"] = None
		data["system"]["-=personalityTraitOptions"] = None
		data["system"]["-=idealOptions"] = None
		data["system"]["-=flawOptions"] = None
		data["system"]["-=bondOptions"] = None

		data["system"]["-=damage"] = None
		data["system"]["-=armorproperties"] = None
		data["system"]["-=weaponproperties"] = None

		return [data]
