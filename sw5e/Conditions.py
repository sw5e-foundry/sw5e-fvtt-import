import sw5e.Entity, utils.text
import re, json

class Conditions(sw5e.Entity.JournalEntry):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.description = utils.text.clean(raw_item, 'description')
		self.contentTypeEnum = utils.text.raw(raw_item, 'contentTypeEnum')
		self.contentType = utils.text.clean(raw_item, 'contentType')
		self.contentSourceEnum = utils.text.raw(raw_item, 'contentSourceEnum')
		self.contentSource = utils.text.clean(raw_item, 'contentSource')
		self.partitionKey = utils.text.clean(raw_item, 'partitionKey')
		self.rowKey = utils.text.clean(raw_item, 'rowKey')

	def getContent(self, val=None):
		content = self.description
		return utils.text.markdownToHtml(content)
