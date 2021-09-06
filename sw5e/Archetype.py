import sw5e.sw5e, utils.text
import re, json

class Archetype(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		self.type = "archetype"

		self.className = utils.text.clean(raw_item, "className")
		self.text = utils.text.clean(raw_item, "text")
		self.text2 = utils.text.raw(raw_item, "text2")
		self.leveledTableHeaders = utils.text.cleanJson(raw_item, "leveledTableHeaders")
		self.leveledTable = utils.text.cleanJson(raw_item, "leveledTable")
		self.imageUrls = utils.text.cleanJson(raw_item, "imageUrls")
		self.casterRatio = utils.text.raw(raw_item, "casterRatio")
		self.casterTypeEnum = utils.text.raw(raw_item, "casterTypeEnum")
		self.casterType = utils.text.clean(raw_item, "casterType")
		self.classCasterTypeEnum = utils.text.raw(raw_item, "classCasterTypeEnum")
		self.classCasterType = utils.text.clean(raw_item, "classCasterType")
		self.features = utils.text.raw(raw_item, "features")
		self.featureRowKeysJson = utils.text.cleanJson(raw_item, "featureRowKeys")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def getDescription(self):
		md_str = f'## {self.name}\n' + self.text
		return utils.text.markdownToHtml(md_str)

	def getImg(self, capitalized=True, index=""):
		if index: index = f'_{index}'
		name = self.name if capitalized else self.name.lower()
		name = re.sub(r'[ /]', r'%20', name)
		name = re.sub(r' (.*?)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/Archetypes/{name}{index}.webp'

	def getData(self, importer):
		data = super().getData(importer)
		data["type"] = self.type
		data["img"] = self.getImg()
		data["data"] = {}
		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["source"] = self.contentSource
		data["data"]["className"] = self.className
		data["data"]["classCasterType"] = self.classCasterType if self.classCasterType != "None" else "",

		return [data]
