import re, json
import utils.text

class Entity:
	def __init__(self, raw_item, old_item, uid, importer):
		self.name = raw_item["name"]
		self.uid = uid
		self.foundry_id = None

		self.timestamp = raw_item["timestamp"]
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

class Item(Entity):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.effects = []
		self.type = None

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["type"] = self.type
		data["img"] = 'icons/svg/item-bag.svg'
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
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.content = utils.text.clean(raw_item, 'content')
		self.contentTypeEnum = utils.text.raw(raw_item, 'contentTypeEnum')
		self.contentType = utils.text.clean(raw_item, 'contentType')
		self.contentSourceEnum = utils.text.raw(raw_item, 'contentSourceEnum')
		self.contentSource = utils.text.clean(raw_item, 'contentSource')
		self.partitionKey = utils.text.clean(raw_item, 'partitionKey')
		self.rowKey = utils.text.clean(raw_item, 'rowKey')

	def getContent(self, val=None):
		content = self.content
		if val: content = re.sub(r'#### \w+', f'#### {val.capitalize()}', content)
		return utils.text.markdownToHtml(content)
