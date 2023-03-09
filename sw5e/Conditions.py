import sw5e.Entity, utils.text
import re, json

class Conditions(sw5e.Entity.JournalEntry):
	def getAttrs(self):
		return super().getAttrs() + [
			"description",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
		]

	def getContent(self, val=None):
		return utils.text.markdownToHtml(self.raw_description)
