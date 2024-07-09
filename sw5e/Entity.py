import re, json
import utils.text

class Entity:
	def __init__(self, raw_entity, uid, importer, importer_version=None):
		self.uid = uid
		self.importer_version = importer_version if importer_version else importer.version

		self.effects = []
		self.broken_links = []
		self.processed = False
		self.foundry_id = None

		self.load(raw_entity)

	def getAttrs(self):
		return [
			"name",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
			"timestamp",
			"eTag",
			"fakeItem",
		]

	def getJsonAttrs(self):
		return []

	def load(self, raw_entity):
		for attr in self.getAttrs(): setattr(self, f'raw_{attr}', utils.text.clean(raw_entity, attr))
		for attr in self.getJsonAttrs(): setattr(self, f'raw_{attr}', utils.text.cleanJson(raw_entity, attr))

		self.name = self.raw_name

	def process(self, importer):
		# if not self.foundry_id: raise AssertionError('Entities should have foundry_id by now', self.uid)
		self.processed = True
		self.broken_links = []

	def getData(self, importer):
		data = {}

		data["name"] = self.name
		data["flags"] = {
			"sw5e-importer": {
				"timestamp": self.raw_timestamp,
				"importer_version": self.importer_version,
				"uid": self.uid,
			}
		}

		return [data]

	def getFile(self, importer):
		return self.__class__.__name__

	def getSubEntities(self, importer):
		return []

	def get(self, entity_type, uid=None, fid_required=True):
		raise NotImplementedError()

	def isValid(self):
		return True

	@classmethod
	def getClass(cls, raw_entity):
		return cls

	@classmethod
	def getUID(cls, raw_entity, entity_type=None):
		uid = entity_type if entity_type else f'{cls.__name__}'

		for key in ('name', 'source', 'sourceName', 'equipmentCategory', 'level', 'subtype'):
			if key in raw_entity:
				value = raw_entity[key]
				if type(value) == str:
					value = value.lower()
					value = re.sub(r'[^\w\s-]', '', value)
					value = re.sub(r'[\s-]+', '_', value).strip('-_')
				uid += f'.{key}-{value}'
		return uid

class Item(Entity):
	def load(self, raw_entity):
		super().load(raw_entity)

	def process(self, importer):
		super().process(importer)

	def getType(self, name=None):
		if name == None:
			name = type(self).__name__.lower()
		name = re.sub(r'[ /]', r'', name)
		return name

	def getImg(self, importer=None):
		return 'icons/svg/item-bag.svg'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["type"] = self.getType()
		data["img"] = self.getImg(importer=importer)
		data["system"] = {}
		data["effects"] = self.effects

		return [data]

class Actor(Entity):
	def load(self, raw_entity):
		super().load(raw_entity)
		self.items = {}

	def getImg(self, importer=None):
		return 'icons/svg/mystery-man.svg'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["img"] = self.getImg(importer=importer)
		data["system"] = {}

		return [data]

	def get(self, entity_type, uid=None, fid_required=True):
		return self.items.get(uid, None)

class JournalEntry(Entity):
	def getContent(self):
		raise NotImplementedError()

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["pages"] = [
			{
				"name": data["name"],
				"_id": "0000000000000000",
				"text": { "content": self.getContent() },
				"src": None,
				"flags": data["flags"],
			}
		]

		return [data]

class Property(JournalEntry):
	def getAttrs(self):
		return super().getAttrs() + [ "content", "contentTypeEnum", "contentType", "contentSourceEnum", "contentSource", "partitionKey", "rowKey" ]

	def getContent(self, val=None):
		content = self.raw_content
		if val: content = re.sub(r'#### [\w-]+', f'#### {val.capitalize()}', content)
		return utils.text.markdownToHtml(content)

class Rule(JournalEntry):
	def getRuleType(self):
		return 'rule'

	def getData(self, importer):
		data = super().getData(importer)[0]
		page = data["pages"][0]

		page["type"] = 'rule'
		page["system"] = {
			"tooltip": self.getContent(),
			"type": self.getRuleType(),
		}

		return [data]
