import sw5e.Equipment, utils.text
import re, json

class Tool(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.activation = 'action'

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.raw_equipmentCategory,
			'no_img': ('Unknown', 'Tool'),
			'default_img': 'systems/sw5e/packs/Icons/Kit/DemolitionsKit.webp',
			# 'plural': False
		}
		return super().getImg(importer=importer, **kwargs)

	def getDescription(self, importer):
		text = self.raw_description
		return utils.text.markdownToHtml(text)

	def getToolType(self):
		tools = {
			"GamingSet": ('game', 'cha'),
			"MusicalInstrument": ('music', 'cha'),
			"ArtisanImplements": ('artisan', 'int'),
			"SpecialistsKit": ('specialist', 'int'),
		}
		category = self.raw_equipmentCategory
		if self.name.find('implements') != -1: category = 'ArtisanImplements'
		elif self.name.find('kit') != -1: category = 'SpecialistsKit'

		if category in tools: return tools[category]
		elif self.name != 'Tool': print(f'		Unable to recognize tool type for {self.name}, {category}')
		return '', 'int'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["toolType"], data["system"]["ability"] = self.getToolType()

		return [data]
