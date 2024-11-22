import utils.text, utils.object
import re, json, copy

_no = {}

class Activity():
	def __init__(self, data=None):
		self.raw_data = copy.deepcopy(data) or {}
		self.data = copy.deepcopy(data) or {}

		self.process()

	def process(self):
		self.id = utils.text.randomID()

	def getType(self):
		return self.__class__.__name__.lower()
	def attrList(self):
		return {
			'name',
			'activation',
			'consumption',
			'description',
			'duration',
			'effects',
			'range',
			'target',
			'uses',
		}
	def getImg(self, importer=None):
		return None
	def getData(self, importer):
		data = {
			"_id": self.id,
			"type": self.getType(),
			"img": self.getImg(importer),
			#"sort": 0,
		}
		for attr in self.attrList():
			if (val := self.getAttrData(importer, attr)) != _no:
				data[attr] = val
		return data
	def getAttrData(self, importer, attr):
		if attr not in ('damage', 'healing'): return self.data.get(attr, _no)
		if val := self.data.get(attr, False): return val.getData()
		return _no

class Attack(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('attack')
		attrs.add('damage')
		return attrs

class Check(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('check')
		return attrs

class Damage(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('damage')
		return attrs

class Enchant(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('effects')
		attrs.add('enchant')
		attrs.add('restrictions')
		return attrs

class Heal(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('healing')
		return attrs

class Save(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('damage')
		attrs.add('effects')
		attrs.add('save')
		return attrs

class Summon(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('bonuses')
		attrs.add('creatureSizes')
		attrs.add('creatureTypes')
		attrs.add('match')
		attrs.add('profiles')
		attrs.add('summon')
		return attrs

class Utility(Activity):
	def attrList(self):
		attrs = super().attrList()
		attrs.add('roll')
		return attrs
