import utils.text
import re, json, copy

class Activity():
	def __init__(self, data=None):
		self.raw_data = copy.deepcopy(data) or {}
		self.data = copy.deepcopy(data) or {}

		self.process()

	def process(self):
		self.id = utils.text.randomID()
		self.processDamage()

	def processDamage(self):
		if "damage" in self.attrList() and "damage" in self.data:
			if "critical" not in self.data["damage"]: self.data["damage"]["critical"] = {}
			if "allow" not in self.data["damage"]["critical"]: self.data["damage"]["critical"]["allow"] = True

	def getType(self):
		return self.__class__.__name__.lower()
	def attrList(self):
		return {
			"name",
			"activation",
			"consumption",
			"description",
			"duration",
			"effects",
			"range",
			"target",
			"uses",
		}
	def getImg(self, importer=None):
		return None
	def getData(self, importer):
		data = {
			"type": self.getType(),
			"_id": self.id,
			"img": self.getImg(importer),
		}
		for attr in self.attrList():
			if attr in self.data and (val := self.data[attr]): data[attr] = val
		return data

class Attack(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("attack")
		attrs.add("damage")
		return attrs

class Check(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("check")
		return attrs

class Damage(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("damage")
		return attrs

class Enchant(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("effects")
		attrs.add("enchant")
		attrs.add("restrictions")
		return attrs

class Heal(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("healing")
		return attrs

class Save(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("damage")
		attrs.add("effects")
		attrs.add("save")
		return attrs

class Summon(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("bonuses")
		attrs.add("creatureSizes")
		attrs.add("creatureTypes")
		attrs.add("match")
		attrs.add("profiles")
		attrs.add("summon")
		return attrs

class Utility(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add("roll")
		return attrs
