import re, json
import utils.text

class Entity:
	def __init__(self, raw_entity, old_entity, uid, importer):
		self.uid = uid
		self.effects = []
		self.load(raw_entity)
		self.process(old_entity, importer)

	def load(self, raw_entity):
		self.name = utils.text.clean(raw_entity, "name")
		self.timestamp = utils.text.clean(raw_entity, "timestamp")

	def process(self, old_entity, importer):
		self.foundry_id = None
		self.importer_version = importer.version
		self.broken_links = False

		if old_entity:
			self.foundry_id = old_entity.foundry_id
			self.effects = old_entity.effects

	def getData(self, importer):
		data = {}

		data["name"] = self.name
		data["flags"] = {
			"timestamp": self.timestamp,
			"importer_version": self.importer_version,
			"uid": self.uid,
		}

		return [data]

	def getFile(self, importer):
		return self.__class__.__name__

	def getSubEntities(self, importer):
		return []

	def get(self, entity_type, uid=None):
		raise NotImplementedError()

	@classmethod
	def getClass(cls, raw_entity):
		return cls

	@classmethod
	def getUID(cls, raw_entity):
		uid = f'{cls.__name__}'

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

	def process(self, old_entity, importer):
		super().process(old_entity, importer)

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
		data["data"] = {}
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
		data["data"] = {}

		return [data]

	def get(self, entity_type, uid=None):
		return self.items.get(uid, None)

class JournalEntry(Entity):
	def getContent(self):
		raise NotImplementedError()

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["content"] = self.getContent()

		return [data]

class Property(JournalEntry):
	def load(self, raw_entity):
		super().load(raw_entity)

		attrs = [ "content", "contentTypeEnum", "contentType", "contentSourceEnum", "contentSource", "partitionKey", "rowKey" ]
		for attr in attrs: setattr(self, f'_{attr}', utils.text.clean(raw_entity, attr))

	def process(self, old_entity, importer):
		super().process(old_entity, importer)

	def getContent(self, val=None):
		content = self._content
		if val: content = re.sub(r'#### [\w-]+', f'#### {val.capitalize()}', content)
		return utils.text.markdownToHtml(content)
