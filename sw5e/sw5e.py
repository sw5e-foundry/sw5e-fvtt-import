import re, json

class Item:
	def __init__(self, raw_item, old_item, importer):
		self.name = raw_item["name"]
		self.id = None
		self.type = None
		self.timestamp = raw_item["timestamp"]
		self.importer_version = importer.version
		self.brokenLinks = False

	def getData(self, importer):
		return {
			"name": self.name,
			"flags": {
				"timestamp": self.timestamp,
				"importer_version": self.importer_version,
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
	def build(cls, raw_item, old_item, importer):
		return cls(raw_item, old_item, importer)
