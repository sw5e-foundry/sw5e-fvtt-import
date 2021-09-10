import re, json

class Item:
	def __init__(self, raw_item, old_item, uid, importer):
		self.name = raw_item["name"]
		self.uid = uid
		self.foundry_id = None
		self.effects = []
		self.type = None
		self.timestamp = raw_item["timestamp"]
		self.importer_version = importer.version
		self.broken_links = False

		if old_item:
			self.foundry_id = old_item.foundry_id
			self.effects = old_item.effects

	def getData(self, importer):
		return [{
			"name": self.name,
			"type": self.type,
			"img": 'icons/svg/item-bag.svg',
			"data": {},
			"flags": {
				"timestamp": self.timestamp,
				"importer_version": self.importer_version,
				"uid": self.uid,
			},
			"effects": self.effects
		}]

	def getFile(self, importer):
		return self.__class__.__name__

	@classmethod
	def getClass(cls, raw_item):
		return cls

	@classmethod
	def getUID(cls, raw_item):
		uid = f'{cls.__name__}'

		for key in ('name', 'source', 'sourceName', 'equipmentCategory', 'level'):
			if key in raw_item:
				value = raw_item[key]
				if type(value) == str:
					value = value.lower()
					value = re.sub(r'[^\w\s-]', '', value)
					value = re.sub(r'[\s-]+', '_', value).strip('-_')
				uid += f'.{key}-{value}'
		return uid
