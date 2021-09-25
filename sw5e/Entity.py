import re, json
import utils.text

class Entity:
	def __init__(self, raw_item, old_item, uid, importer):
		self.uid = uid
		self.load(raw_item)
		self.process(old_item, importer)

	def load(self, raw_item):
		self.name = raw_item["name"]
		self.timestamp = raw_item["timestamp"]

	def process(self, old_item, importer):
		self.foundry_id = None
		self.importer_version = importer.version
		self.broken_links = False

		if old_item:
			self.foundry_id = old_item.foundry_id
			self.effects = old_item.effects

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

	def getSubItems(self, importer):
		return []

	@classmethod
	def getClass(cls, raw_item):
		return cls

	@classmethod
	def getUID(cls, raw_item):
		uid = f'{cls.__name__}'

		for key in ('name', 'source', 'sourceName', 'equipmentCategory', 'level', 'subtype'):
			if key in raw_item:
				value = raw_item[key]
				if type(value) == str:
					value = value.lower()
					value = re.sub(r'[^\w\s-]', '', value)
					value = re.sub(r'[\s-]+', '_', value).strip('-_')
				uid += f'.{key}-{value}'
		return uid

class Item(Entity):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.effects = []

	def getType(self, name=None):
		if name == None:
			name = type(self).__name__.lower()
		name = re.sub(r'[ /]', r'', name)
		return name

	def getImg(self):
		return 'icons/svg/item-bag.svg'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["type"] = self.getType()
		data["img"] = self.getImg()
		data["data"] = {}
		data["effects"] = self.effects

		return [data]

class Actor(Entity):
	pass

class JournalEntry(Entity):
	def getData(self, importer):
		data = super().getData(importer)[0]

		data["content"] = self.getContent()

		return [data]

	def getContent(self):
		raise NotImplementedError()

class Property(JournalEntry):
	def load(self, raw_item):
		super().load(raw_item)

		self.content = utils.text.clean(raw_item, 'content')
		self.contentTypeEnum = utils.text.raw(raw_item, 'contentTypeEnum')
		self.contentType = utils.text.clean(raw_item, 'contentType')
		self.contentSourceEnum = utils.text.raw(raw_item, 'contentSourceEnum')
		self.contentSource = utils.text.clean(raw_item, 'contentSource')
		self.partitionKey = utils.text.clean(raw_item, 'partitionKey')
		self.rowKey = utils.text.clean(raw_item, 'rowKey')

	def process(self, old_item, importer):
		super().process(old_item, importer)

	def getContent(self, val=None):
		content = self.content
		if val: content = re.sub(r'#### \w+', f'#### {val.capitalize()}', content)
		return utils.text.markdownToHtml(content)
