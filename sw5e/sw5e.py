import re, json

class Item:
	def __init__(self, raw_item, old_item, uid, importer):
		self.name = raw_item["name"]
		self.uid = uid
		self.foundry_id = None
		self.type = None
		self.timestamp = raw_item["timestamp"]
		self.importer_version = importer.version
		self.broken_links = False

		if old_item and old_item.foundry_id:
			self.foundry_id = old_item.foundry_id

	def getData(self, importer):
		return {
			"name": self.name,
			"flags": {
				"timestamp": self.timestamp,
				"importer_version": self.importer_version,
				"uid": self.uid,
			}
		}

	def matches(self, *args, **kwargs):
		if len(args) >= 1:
			new_item = args[0]
			if new_item["name"] != self.name: return False
		for kw in kwargs:
			if getattr(self, kw) != kwargs[kw]:
				return False
		return True

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
					value = re.sub(r'[^\w\s\-_]', '', value)
					value = re.sub(r'[\-_\s]+', '_', value).strip('-_')
				uid += f'.{key}-{value}'
		return uid
