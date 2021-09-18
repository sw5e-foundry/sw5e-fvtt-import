import sw5e.Entity, utils.text
import re, json

class Feat(sw5e.Entity.Item):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.type = 'feat'

		self.prerequisite = utils.text.clean(raw_item, "prerequisite")
		self.text = utils.text.clean(raw_item, "text")
		self.attributesIncreased = utils.text.cleanJson(raw_item, "attributesIncreased")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

		self.uses, self.recharge = utils.text.getUses(self.text, self.name)
		self.action = utils.text.getActivation(self.text, self.uses, self.recharge)

	def getImg(self):
		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		return f'systems/sw5e/packs/Icons/Feats/{name}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["img"] = self.getImg()

		data["data"]["description"] = { "value": utils.text.markdownToHtml(self.text) }
		data["data"]["requirements"] = self.prerequisite
		data["data"]["source"] = self.contentSource

		data["data"]["activation"] = {
			"type": self.action,
			"cost": 1
		} if self.action != 'none' else {}

		#TODO: extract duration, target, range, uses, consume, damage and other rolls
		data["data"]["duration"] = {}
		data["data"]["target"] = {}
		data["data"]["range"] = {}
		data["data"]["uses"] = {
			"value": 0,
			"max": self.uses,
			"per": self.recharge
		}
		data["data"]["consume"] = {}
		data["data"]["ability"] = ''
		data["data"]["actionType"] = ''
		data["data"]["attackBonus"] = 0
		data["data"]["chatFlavor"] = ''
		data["data"]["critical"] = None
		data["data"]["damage"] = {
			"parts": [],
			"versatile": '',
		}
		data["data"]["formula"] = ''
		data["data"]["save"] = {}
		data["data"]["recharge"] = ''

		return [data]
