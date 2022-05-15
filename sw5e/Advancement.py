import utils.text
import re, json

class Advancement():
	def getType(self):
		return self.__class__.__name__
	def getData(self, importer):
		data = {
			"_id": utils.text.randomID(),
			"type": self.getType(),
			"configuration": {},
			"value": {},
		}
		return data

class HitPoints(Advancement):
	pass

class ScaleValue(Advancement):
	def __init__(self, name="Scale Value", configuration={}):
		self.name = name
		self.configuration = configuration
		self.configuration["identifier"] |= utils.text.slugify(name, capitalized=False)

	def getData(self, importer):
		data = super().getData(importer)

		data["configuration"] = self.configuration
		data["title"] = self.name

		return data

class ItemGrant(Advancement):
	def __init__(self, name=None, uids=[], optional=False, level=1, class_restriction=""):
		self.name = name
		self.configuration = {
			"items": uids,
			"optional": optional
		}
		self.level = level
		self.class_restriction = class_restriction

	def getData(self, importer):
		data = super().getData(importer)

		data["configuration"] = self.configuration
		data["level"] = self.level
		if self.name: data["title"] = self.name
		data["classRestriction"] = self.class_restriction

		return data
