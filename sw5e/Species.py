import sw5e.sw5e, utils.text
import re, json

class Species(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.type = "species"

		self.skinColorOptions = utils.text.clean(raw_item, "skinColorOptions")
		self.hairColorOptions = utils.text.clean(raw_item, "hairColorOptions")
		self.eyeColorOptions = utils.text.clean(raw_item, "eyeColorOptions")
		self.distinctions = utils.text.clean(raw_item, "distinctions")
		self.heightAverage = utils.text.clean(raw_item, "heightAverage")
		self.heightRollMod = utils.text.clean(raw_item, "heightRollMod")
		self.weightAverage = utils.text.clean(raw_item, "weightAverage")
		self.weightRollMod = utils.text.clean(raw_item, "weightRollMod")
		self.homeworld = utils.text.clean(raw_item, "homeworld")
		self.flavorText = utils.text.clean(raw_item, "flavorText")
		self.colorScheme = utils.text.clean(raw_item, "colorScheme")
		self.manufacturer = utils.text.clean(raw_item, "manufacturer")
		self.language = utils.text.clean(raw_item, "language")
		self.traits = utils.text.cleanJson(raw_item, "trait")
		self.abilitiesIncreased = utils.text.cleanJson(raw_item, "abilitiesIncreased")
		self.imageUrls = utils.text.cleanJson(raw_item, "imageUrls")
		self.size = utils.text.clean(raw_item, "size")
		self.halfHumanTableEntries = utils.text.cleanJson(raw_item, "halfHumanTableEntries")
		self.features = utils.text.clean(raw_item, "features")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def getImg(self):
		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		name = re.sub(r'[,]', r'', name)
		return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getDescription(self):
		return utils.text.markdownToHtml(self.flavorText)

	def getTraits(self):
		traits = [f'<p><em><strong>{trait["Name"]}.</strong></em> {trait["Description"]}</p>' for trait in self.traits]
		return '\n'.join(traits)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["img"] = self.getImg()

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["source"] = self.contentSource
		data["data"]["traits"] = { "value": self.getTraits() }
		data["data"]["skinColorOptions"] = { "value": self.skinColorOptions}
		data["data"]["hairColorOptions"] = { "value": self.hairColorOptions}
		data["data"]["eyeColorOptions"] = { "value": self.eyeColorOptions}
		data["data"]["colorScheme"] = { "value": self.colorScheme}
		data["data"]["distinctions"] = { "value": self.distinctions}
		data["data"]["heightAverage"] = { "value": self.heightAverage}
		data["data"]["heightRollMod"] = { "value": self.heightRollMod}
		data["data"]["weightAverage"] = { "value": self.weightAverage}
		data["data"]["weightRollMod"] = { "value": self.weightRollMod}
		data["data"]["homeworld"] = { "value": self.homeworld}
		data["data"]["slanguage"] = { "value": self.language}
		data["data"]["damage"] = { "parts": []}
		data["data"]["armorproperties"] = { "parts": []}
		data["data"]["weaponproperties"] = { "parts": []}

		return [data]
