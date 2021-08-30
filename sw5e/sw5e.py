import re

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

	@staticmethod
	def cleanStr(string):
		if string:
			string = ' '.join(string.split(' '))
			string = re.sub(r'\ufffd', r'—', string)
			string = re.sub(r'\r', r'', string)
			string = re.sub(r'\n\n', r'\n', string)
			return string

	@staticmethod
	def markdownToHtml(lines):
		if lines:
			if type(lines) == str: lines = lines.split('\n')
			lines = list(filter(None, lines))

			inList = False
			for i in range(len(lines)):
				lines[i] = Item.cleanStr(lines[i])

				if lines[i].startswith(r'- '):
					lines[i] = f'<li>{lines[i][2:]}</li>'

					if not inList:
						lines[i] = f'<ul>\n{lines[i]}'
						inList = True
				else:
					if lines[i].startswith(r'#'):
						count = lines[i].find(' ')
						lines[i] = f'<h{count-1}>{lines[i][count+1:]}</h{count-1}>'
					elif not lines[i].startswith(r'<'):
						lines[i] = f'<p>{lines[i]}</p>'

					if inList:
						lines[i] = f'</ul>\n{lines[i]}'
						inList = False

				lines[i] = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', lines[i])
				lines[i] = re.sub(r'\*(.*?)\*', r'<em>\1</em>', lines[i])
				lines[i] = re.sub(r'_(.*?)_', r'<em>\1</em>', lines[i])
			return '\r\n'.join(lines)

	def matches(self, *args, **kwargs):
		if len(args) >= 1:
			new_item = args[0]
			if new_item["name"] != self.name: return False
		for kw in kwargs:
			if getattr(self, kw) != kwargs[kw]:
				return False
		return True
