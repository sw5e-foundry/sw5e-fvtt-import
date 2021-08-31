import sw5e.sw5e
import re

class Archetype(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		self.type = "archetype"

		def raw(attr): return attr and raw_item[attr]
		def clean(attr): return attr and self.cleanStr(raw_item[attr])
		def cleanJson(attr): return attr and (clean(attr+"Json") or '  ')[2:-2].split('","')

		self.className = clean("className")
		self.text = clean("text")
		self.text2 = raw("text2")
		self.leveledTableHeaders = cleanJson("leveledTableHeaders")
		self.leveledTable = cleanJson("leveledTable")
		self.imageUrls = cleanJson("imageUrls")
		self.casterRatio = raw("casterRatio")
		self.casterTypeEnum = raw("casterTypeEnum")
		self.casterType = clean("casterType")
		self.classCasterTypeEnum = raw("classCasterTypeEnum")
		self.classCasterType = clean("classCasterType")
		self.features = raw("features")
		self.featureRowKeysJson = cleanJson("featureRowKeys")
		self.contentTypeEnum = raw("contentTypeEnum")
		self.contentType = clean("contentType")
		self.contentSourceEnum = raw("contentSourceEnum")
		self.contentSource = clean("contentSource")
		self.partitionKey = clean("partitionKey")
		self.rowKey = clean("rowKey")

	def getDescription(self):
		md_str = f'## {self.name}\n' + self.text
		return self.markdownToHtml(md_str)

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
		return data
