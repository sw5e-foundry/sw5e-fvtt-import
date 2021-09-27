import sw5e.Entity, utils.text
import re, json

class Background(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.flavorText = utils.text.clean(raw_item, "flavorText")
		self.flavorName = utils.text.clean(raw_item, "flavorName")
		self.flavorDescription = utils.text.clean(raw_item, "flavorDescription")
		self.flavorOptions = utils.text.cleanJson(raw_item, "flavorOptions")
		self.skillProficiencies = utils.text.clean(raw_item, "skillProficiencies")
		self.toolProficiencies = utils.text.clean(raw_item, "toolProficiencies")
		self.languages = utils.text.clean(raw_item, "languages")
		self.equipment = utils.text.clean(raw_item, "equipment")
		self.suggestedCharacteristics = utils.text.clean(raw_item, "suggestedCharacteristics")
		self.featureName = utils.text.clean(raw_item, "featureName")
		self.featureText = utils.text.clean(raw_item, "featureText")
		self.featOptions = utils.text.cleanJson(raw_item, "featOptions")
		self.personalityTraitOptions = utils.text.cleanJson(raw_item, "personalityTraitOptions")
		self.idealOptions = utils.text.cleanJson(raw_item, "idealOptions")
		self.flawOptions = utils.text.cleanJson(raw_item, "flawOptions")
		self.bondOptions = utils.text.cleanJson(raw_item, "bondOptions")
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

	def getImg(self):
		name = self.name
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Backgrounds/{name}.webp'

	def getFlavorText(self):
		text = self.flavorText
		return utils.text.markdownToHtml(text)

	def getFlavorDescription(self):
		text = self.flavorDescription
		if text and (match := re.search(r'\.\s*\|\s*d\d+\s*\|', text)):
			text = text[:match.start()+1]
		return utils.text.markdownToHtml(text)

	def getTable(self, table, name):
		if self.flavorOptions:
			content = [ (
				opt["Roll"],
				(opt["Name"] or '') + (': ' if (opt["Name"] and opt["Description"]) else '') + (opt["Description"] or '')
			) for opt in table ]
			header = [ f'[[/r d{len(content)} # {name}]]', name ]
			align = [ 'center', 'center' ]
			return utils.text.makeTable(content, header=header, align=align)

	def getFeatOptions(self, importer):
		if self.featOptions:
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
				opt["Roll"],
				getLink(opt["Name"])
			) for opt in self.featOptions ]
			header = [ f'[[/r d{len(content)} # Feat]]', 'Feat' ]
			align = [ 'center', 'center' ]
			return utils.text.makeTable(content, header=header, align=align)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["flavorText"] = { "value": self.getFlavorText() }
		data["data"]["flavorName"] = { "value": self.flavorName }
		data["data"]["flavorDescription"] = { "value": self.getFlavorDescription() }
		data["data"]["flavorOptions"] = { "value": self.getTable(self.flavorOptions, self.flavorName) }
		data["data"]["skillProficiencies"] = { "value": self.skillProficiencies }
		data["data"]["toolProficiencies"] = { "value": self.toolProficiencies }
		data["data"]["languages"] = { "value": self.languages }
		data["data"]["equipment"] = { "value": self.equipment }
		data["data"]["suggestedCharacteristics"] = { "value": self.suggestedCharacteristics }
		data["data"]["featureName"] = { "value": self.featureName }
		data["data"]["featureText"] = { "value": self.featureText }
		data["data"]["featOptions"] = { "value": self.getFeatOptions(importer) }
		data["data"]["personalityTraitOptions"] = { "value": self.getTable(self.personalityTraitOptions, 'Personality Trait') }
		data["data"]["idealOptions"] = { "value": self.getTable(self.idealOptions, 'Ideal') }
		data["data"]["flawOptions"] = { "value": self.getTable(self.flawOptions, 'Flaw') }
		data["data"]["bondOptions"] = { "value": self.getTable(self.bondOptions, 'Bond') }

		data["data"]["source"] = self.contentSource

		data["data"]["damage"] = { "parts": []}
		data["data"]["armorproperties"] = { "parts": []}
		data["data"]["weaponproperties"] = { "parts": []}

		return [data]
